# AGI Command Center - Comprehensive Bug Audit & Fixes
**Date:** July 4, 2026  
**Version:** 1.0.0 → 1.0.1  
**Status:** CRITICAL & HIGH PRIORITY FIXES IDENTIFIED

---

## 🔴 CRITICAL BUGS

### BUG #1: Kalman Filter - Division by Zero Risk
**File:** `src/core/data_engine.py` (Line 216)  
**Severity:** CRITICAL  
**Category:** Mathematical Error

#### Issue
```python
kalman_gain = predicted_error / (predicted_error + r)
```
If `predicted_error` is very small (near 0) and `r` is also small, this can cause numerical instability. However, the main issue is **no guard against NaN propagation**.

#### Root Cause
- If `data.iloc[i]` contains NaN, it propagates through the entire series
- No validation that input series doesn't contain NaN values
- No checks for negative error estimates (should never happen but numerical errors can cause it)

#### Fix
```python
def apply_kalman_filter(self, data: pd.Series, q: float = 0.005, r: float = 0.12) -> pd.Series:
    """Apply Kalman filter with error handling"""
    # Validate input
    if data is None or len(data) == 0:
        logger.error("Kalman filter: Empty data series")
        return data
    
    # Remove NaN values and warn
    if data.isna().any():
        logger.warning(f"Kalman filter: Found {data.isna().sum()} NaN values, forward-filling")
        data = data.fillna(method='ffill').fillna(method='bfill')
    
    if not np.isfinite(data.iloc[0]):
        logger.error("Kalman filter: First value is not finite")
        return data
    
    n = len(data)
    estimates = np.zeros(n)
    errors = np.zeros(n)
    
    # Initial state with bounds checking
    estimates[0] = float(data.iloc[0])
    errors[0] = 1.0
    
    for i in range(1, n):
        # Prediction step
        predicted_estimate = estimates[i - 1]
        predicted_error = errors[i - 1] + q
        
        # Ensure error stays positive (safeguard)
        predicted_error = max(predicted_error, 1e-8)
        
        # Guard against NaN in measurement
        measurement = float(data.iloc[i])
        if not np.isfinite(measurement):
            estimates[i] = predicted_estimate  # Use prediction if measurement is bad
            errors[i] = predicted_error
            continue
        
        # Update step
        denominator = predicted_error + r
        if denominator <= 0:
            logger.warning(f"Kalman filter: Denominator <= 0 at step {i}")
            kalman_gain = 0.5  # Default to 50/50 weighting
        else:
            kalman_gain = predicted_error / denominator
        
        # Ensure Kalman gain is in valid range [0, 1]
        kalman_gain = np.clip(kalman_gain, 0, 1)
        
        estimates[i] = predicted_estimate + kalman_gain * (measurement - predicted_estimate)
        errors[i] = (1 - kalman_gain) * predicted_error
    
    return pd.Series(estimates, index=data.index)
```

---

### BUG #2: Data Validation - Missing Column Checks
**File:** `src/core/data_engine.py` (Lines 137-142)  
**Severity:** CRITICAL  
**Category:** KeyError Exception Risk

#### Issue
```python
if not (data['Low'] <= data['Open']).all() or not (data['Open'] <= data['High']).all():
    errors.append("OHLC ordering violated")
```

**Problem:** If DataFrame doesn't have 'Low', 'Open', 'High', 'Volume' columns, this will raise `KeyError` and crash the validation function.

#### Fix
```python
def validate_data_integrity(self, data: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
    """Perform comprehensive data validation with robust error handling"""
    errors = []
    
    # Check if DataFrame is empty
    if data is None or data.empty:
        errors.append("DataFrame is None or empty")
        return False, errors
    
    # Check required columns exist
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
        return False, errors
    
    # Check for NaN values
    nan_count = data.isna().sum().sum()
    if nan_count > len(data) * 0.1:  # Alert if > 10% NaN
        errors.append(f"Found {nan_count} NaN values ({nan_count/len(data)*100:.1f}%)")
    
    # Check OHLC ordering with safe access
    try:
        invalid_low_open = (data['Low'] > data['Open']).any()
        invalid_open_high = (data['Open'] > data['High']).any()
        invalid_low_high = (data['Low'] > data['High']).any()
        
        if invalid_low_open or invalid_open_high or invalid_low_high:
            errors.append("OHLC ordering violated (Low > Open or Open > High or Low > High)")
    except TypeError as e:
        errors.append(f"OHLC comparison error (type mismatch): {e}")
    
    # Check volume is non-negative
    try:
        if (data['Volume'] < 0).any():
            errors.append("Negative volume detected")
    except TypeError:
        errors.append("Volume column contains non-numeric values")
    
    # Check for duplicate timestamps
    if data.index.duplicated().any():
        duplicate_count = data.index.duplicated().sum()
        errors.append(f"Found {duplicate_count} duplicate timestamps")
    
    # Check for zero volume (suspicious)
    zero_volume_count = (data['Volume'] == 0).sum()
    if zero_volume_count > len(data) * 0.2:  # Alert if > 20% zero volume
        errors.append(f"Found {zero_volume_count} zero-volume bars ({zero_volume_count/len(data)*100:.1f}%)")
    
    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Data validation failed for {symbol}: {errors}")
    
    return is_valid, errors
```

---

### BUG #3: Cache Manager - JSON Deserialization Failure
**File:** `src/core/cache_manager.py` (Lines 93-96)  
**Severity:** CRITICAL  
**Category:** Silent Failure

#### Issue
```python
try:
    return json.loads(value.decode('utf-8'))
except:  # BUG: Bare except clause swallows all errors
    return value.decode('utf-8')
```

**Problems:**
1. Bare `except` clause catches all exceptions (KeyboardInterrupt, SystemExit, etc.)
2. Silently returns wrong type if JSON parsing fails
3. No logging of what went wrong

#### Fix
```python
def get(self, key: str) -> Optional[Any]:
    """Get cache value with proper error handling"""
    if self.backend == 'memory':
        if key in self.ttl_map and datetime.now() > self.ttl_map[key]:
            # Expired - clean up
            try:
                del self.memory_cache[key]
                del self.ttl_map[key]
            except KeyError:
                pass  # Already deleted
            return None
        return self.memory_cache.get(key)
    
    elif self.backend == 'redis' and self.redis_client:
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to decode and deserialize
            try:
                decoded = value.decode('utf-8') if isinstance(value, bytes) else value
                # Try JSON deserialization
                try:
                    return json.loads(decoded)
                except json.JSONDecodeError:
                    # Not JSON, return as string
                    logger.debug(f"Cache key {key} is not valid JSON, returning as string")
                    return decoded
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode cache value for key {key}: {e}")
                return None
            
        except redis.RedisError as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting cache key {key}: {e}")
            return None
    
    return None
```

---

### BUG #4: FeedManager - Empty Tick List Aggregation
**File:** `src/core/feed_manager.py` (Lines 117-119)  
**Severity:** HIGH  
**Category:** Logic Error

#### Issue
```python
ticks = self.ticks[symbol]
prices = [t.price for t in ticks]
volumes = [t.volume for t in ticks]

bar = OHLCV(
    open=prices[0],  # BUG: IndexError if empty list
    ...
)
```

**Problem:** If `ticks` list is empty, `prices[0]` will raise `IndexError`.

#### Fix
```python
def aggregate_to_bar(self, symbol: str, timeframe: str) -> Optional[OHLCV]:
    """Aggregate ticks into OHLCV bar with validation"""
    if symbol not in self.ticks or len(self.ticks[symbol]) == 0:
        logger.debug(f"No ticks available for {symbol}")
        return None
    
    ticks = self.ticks[symbol]
    
    # Validate tick data
    if not all(hasattr(t, 'price') and hasattr(t, 'volume') for t in ticks):
        logger.error(f"Invalid tick structure for {symbol}")
        return None
    
    prices = [t.price for t in ticks if np.isfinite(t.price)]
    volumes = [t.volume for t in ticks if t.volume >= 0]
    
    if not prices or not volumes:
        logger.warning(f"No valid price/volume data for {symbol}")
        return None
    
    try:
        bar = OHLCV(
            open=float(prices[0]),
            high=float(max(prices)),
            low=float(min(prices)),
            close=float(prices[-1]),
            volume=int(sum(volumes)),
            timestamp=ticks[-1].timestamp
        )
        return bar
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to create bar for {symbol}: {e}")
        return None
```

---

### BUG #5: Time Series Coherence - Placeholder Implementation
**File:** `src/core/data_engine.py` (Lines 154-174)  
**Severity:** HIGH  
**Category:** Non-functional Code

#### Issue
```python
def check_time_series_coherence(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    for tf, data in data_dict.items():
        coherence_scores[tf] = 0.95  # Placeholder - always returns 0.95!
```

**Problem:** Always returns 0.95 regardless of actual data. This is completely non-functional.

#### Fix
```python
def check_time_series_coherence(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """
    Verify time-series coherence across multiple timeframes.
    Validates that higher TF candles aggregate correctly from lower TF.
    """
    coherence_scores = {}
    
    timeframe_order = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1mo']
    
    for tf, data in data_dict.items():
        if data is None or data.empty:
            coherence_scores[tf] = 0.0
            logger.warning(f"No data for timeframe {tf}")
            continue
        
        # Check basic structure
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_cols):
            coherence_scores[tf] = 0.0
            continue
        
        # Score based on multiple criteria
        score = 1.0
        
        # 1. Check for gaps in timestamps (should be regular)
        if len(data) > 1:
            time_diffs = pd.Series(data.index).diff()
            # Allow 10% variance in time intervals
            if time_diffs.std() / time_diffs.mean() > 0.1:
                score -= 0.1
        
        # 2. Check OHLC consistency
        high_low_valid = ((data['High'] >= data['Low']).all() and 
                         (data['High'] >= data['Open']).all() and
                         (data['High'] >= data['Close']).all())
        if not high_low_valid:
            score -= 0.2
        
        # 3. Check for suspicious volume patterns
        if (data['Volume'] == 0).sum() / len(data) > 0.2:
            score -= 0.1
        
        # 4. Check for outliers (>3 std from mean)
        close_returns = data['Close'].pct_change()
        outlier_count = (abs(close_returns - close_returns.mean()) > 3 * close_returns.std()).sum()
        if outlier_count / len(data) > 0.05:
            score -= 0.15
        
        coherence_scores[tf] = max(0.0, score)
    
    logger.info(f"Timeframe coherence scores: {coherence_scores}")
    return coherence_scores
```

---

## 🟠 HIGH PRIORITY BUGS

### BUG #6: FeedManager - Memory Leak from Unlimited Tick Storage
**File:** `src/core/feed_manager.py` (Line 96)  
**Severity:** HIGH  
**Category:** Memory Management

#### Issue
```python
self.ticks[symbol].append(tick)  # Unlimited growth!
```

**Problem:** Ticks are stored indefinitely in memory with no size limits. Over time this will consume all available RAM.

#### Fix
```python
def __init__(self, config: Dict, max_ticks_per_symbol: int = 10000):
    self.config = config
    self.ticks: Dict[str, List[Tick]] = {}
    self.bars: Dict[str, List[OHLCV]] = {}
    self.callbacks: Dict[str, List[Callable]] = {}
    self.order_book: Dict[str, Dict] = {}
    self.is_connected = False
    self.max_ticks_per_symbol = max_ticks_per_symbol

def process_tick(self, tick: Tick):
    """Process incoming tick with memory management"""
    if tick.symbol not in self.ticks:
        self.ticks[tick.symbol] = []
    
    self.ticks[tick.symbol].append(tick)
    
    # Keep only the last N ticks
    if len(self.ticks[tick.symbol]) > self.max_ticks_per_symbol:
        self.ticks[tick.symbol] = self.ticks[tick.symbol][-self.max_ticks_per_symbol:]
    
    # Trigger callbacks
    if 'tick' in self.callbacks:
        for callback in self.callbacks['tick']:
            try:
                callback(tick)
            except Exception as e:
                logger.error(f"Callback error: {e}")
```

---

### BUG #7: Data Engine - Unimplemented Methods Return Empty Data
**File:** `src/core/data_engine.py` (Lines 50-116)  
**Severity:** HIGH  
**Category:** Non-functional Code

#### Issue
All data ingestion methods are stubs that return empty DataFrames:
```python
def ingest_futures_data(self, symbol: str, timeframes: List[str]) -> pd.DataFrame:
    data = {}
    for tf in timeframes:
        data[tf] = pd.DataFrame()  # Always empty!
    return data
```

#### Fix - Add Real Implementation
See new `src/core/real_data_engine.py` (provided separately) with actual API integration.

---

### BUG #8: Cache Manager - Race Condition in get_ohlcv
**File:** `src/core/cache_manager.py` (Lines 117-132)  
**Severity:** MEDIUM-HIGH  
**Category:** Concurrency

#### Issue
```python
def get_ohlcv(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    key = f"ohlcv:{symbol}:{timeframe}"
    value = self.get(key)  # Returns list of dicts
    if value:
        return pd.DataFrame(value)  # Could fail if value structure changed
```

**Problem:** If cache expires between `get()` and `pd.DataFrame()` creation, or if value format is inconsistent, this will fail.

#### Fix
```python
def get_ohlcv(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """Get cached OHLCV data with type validation"""
    key = f"ohlcv:{symbol}:{timeframe}"
    value = self.get(key)
    
    if value is None:
        return None
    
    try:
        # Validate that value is a list of dicts
        if not isinstance(value, list):
            logger.warning(f"Cache key {key} has unexpected type: {type(value)}")
            return None
        
        if len(value) == 0:
            return pd.DataFrame()
        
        # Validate first element is dict-like
        if not isinstance(value[0], dict):
            logger.warning(f"Cache key {key} contains non-dict elements")
            return None
        
        df = pd.DataFrame(value)
        
        # Validate required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required):
            logger.warning(f"Cached OHLCV for {symbol}/{timeframe} missing columns")
            return None
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to reconstruct OHLCV DataFrame for {key}: {e}")
        return None
```

---

## 🟡 MEDIUM PRIORITY BUGS

### BUG #9: FeedManager - No Bid-Ask Validation
**File:** `src/core/feed_manager.py` (Lines 147-167)  
**Severity:** MEDIUM  
**Category:** Logic Error

#### Issue
```python
def get_bid_ask_spread(self, symbol: str) -> float:
    bid = book['bids'][0][0]
    ask = book['asks'][0][0]
    spread_bps = (ask - bid) / bid * 10000
```

**Problem:** No validation that `bid < ask`. If data is corrupted, spread can be negative or infinite.

#### Fix
```python
def get_bid_ask_spread(self, symbol: str) -> Optional[float]:
    """Get current bid-ask spread with validation"""
    if symbol not in self.order_book:
        return None
    
    book = self.order_book[symbol]
    if len(book['bids']) == 0 or len(book['asks']) == 0:
        return None
    
    bid = float(book['bids'][0][0])
    ask = float(book['asks'][0][0])
    
    # Validate bid < ask and both are positive
    if bid <= 0 or ask <= 0:
        logger.warning(f"Invalid bid/ask for {symbol}: bid={bid}, ask={ask}")
        return None
    
    if bid >= ask:
        logger.warning(f"Inverted bid-ask for {symbol}: bid={bid}, ask={ask}")
        return None
    
    spread_bps = (ask - bid) / bid * 10000
    
    # Sanity check: spread should be reasonable (typically < 1000 bps = 10%)
    if spread_bps > 1000:
        logger.warning(f"Unusual spread for {symbol}: {spread_bps} bps")
    
    return spread_bps
```

---

### BUG #10: DataEngine - No Error Context in Validation
**File:** `src/core/data_engine.py` (Lines 118-152)  
**Severity:** MEDIUM  
**Category:** Error Reporting

#### Issue
When validation fails, no information about which rows failed or specific problematic values.

#### Fix
```python
def validate_data_integrity(self, data: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
    """Enhanced validation with detailed error context"""
    errors = []
    
    # ... (previous checks) ...
    
    # Enhanced OHLC validation with row-level details
    try:
        ohlc_violations = (data['Low'] > data['Open']) | (data['Open'] > data['High']) | (data['Low'] > data['High'])
        if ohlc_violations.any():
            bad_rows = data[ohlc_violations].head(5)  # Show first 5
            errors.append(f"OHLC ordering violated in {ohlc_violations.sum()} rows (examples: {bad_rows.index.tolist()})")
    except Exception as e:
        errors.append(f"OHLC validation error: {e}")
    
    # Enhanced volume validation
    try:
        neg_volume = (data['Volume'] < 0).any()
        zero_volume = (data['Volume'] == 0).sum()
        if neg_volume:
            bad_rows = data[data['Volume'] < 0].head(5)
            errors.append(f"Negative volume found: {bad_rows.index.tolist()}")
        if zero_volume > 0:
            logger.info(f"Found {zero_volume} zero-volume bars for {symbol}")
    except Exception as e:
        errors.append(f"Volume validation error: {e}")
    
    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Data validation failed for {symbol}: {errors}")
    else:
        logger.info(f"Data validation passed for {symbol} ({len(data)} rows)")
    
    return is_valid, errors
```

---

## 📋 Summary Table

| Bug ID | File | Severity | Type | Status |
|--------|------|----------|------|--------|
| #1 | data_engine.py | 🔴 CRITICAL | Math/NaN | NEEDS FIX |
| #2 | data_engine.py | 🔴 CRITICAL | KeyError | NEEDS FIX |
| #3 | cache_manager.py | 🔴 CRITICAL | Silent Fail | NEEDS FIX |
| #4 | feed_manager.py | 🟠 HIGH | Logic | NEEDS FIX |
| #5 | data_engine.py | 🟠 HIGH | Non-functional | NEEDS FIX |
| #6 | feed_manager.py | 🟠 HIGH | Memory Leak | NEEDS FIX |
| #7 | data_engine.py | 🟠 HIGH | Non-functional | NEEDS IMPL |
| #8 | cache_manager.py | 🟠 HIGH | Concurrency | NEEDS FIX |
| #9 | feed_manager.py | 🟡 MEDIUM | Validation | NEEDS FIX |
| #10 | data_engine.py | 🟡 MEDIUM | Error Info | NEEDS FIX |

---

## ✅ Recommendations

1. **Immediate:** Fix bugs #1-3 (CRITICAL) before any production use
2. **Before deployment:** Fix bugs #4-8 (HIGH)
3. **Next iteration:** Address bugs #9-10 (MEDIUM)
4. **Add comprehensive unit tests** for all data processing paths
5. **Add integration tests** for data validation pipeline
6. **Add monitoring/alerting** for cache misses and validation failures
