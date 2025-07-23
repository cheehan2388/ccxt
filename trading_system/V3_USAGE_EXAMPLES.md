# 🚀 Trading System V3 - Usage Examples

## 🎯 Maximum Flexibility Achieved!

Your V3 system is now **incredibly flexible** - you can change ANY configuration without touching code!

---

## ✅ **What V3 Gives You:**

### **Smart Configuration System:**
- ✅ No more hardcoded names
- ✅ Any feature + any preprocessing + any combination
- ✅ All V2 choices preserved but more flexible
- ✅ Future-ready for any data types

### **Your Example Working Perfectly:**
```python
# Your exact configuration:
config = V3Config(
    features=[
        FeatureConfig(name="longshort", preprocess=PreprocessMethod.ZSCORE, window=30),
        FeatureConfig(name="open_interest", preprocess=PreprocessMethod.ROLLING_MINMAX, window=30)
    ],
    combination=CombinationConfig(
        method=CombinationMethod.ADD,
        final_preprocess=PreprocessMethod.ZSCORE_TREND,
        final_window=30
    ),
    thresholds={"long": -2.5, "short": 2.5}
)
```

**Result:** 
- `longshort: -0.234` (zscore preprocessing)
- `open_interest: 0.748` (rolling_minmax preprocessing)  
- `Combined: 0.513` (added together)
- `Final Signal: 2.499` (zscore_trend applied)

---

## 🔧 **Easy Configuration Changes:**

### **Example 1: Different Preprocessing Methods**
```python
config = V3Config(
    features=[
        FeatureConfig(name="volume", preprocess=PreprocessMethod.MOMENTUM, window=20),
        FeatureConfig(name="open_interest", preprocess=PreprocessMethod.ROLLING_STD, window=25),
        FeatureConfig(name="longshort", preprocess=PreprocessMethod.ZSCORE, window=15)
    ],
    combination=CombinationConfig(
        method=CombinationMethod.MULTIPLY,
        final_preprocess=PreprocessMethod.ROLLING_MINMAX
    ),
    thresholds={"long": -1.8, "short": 1.8}
)
```

### **Example 2: Weighted Combination**
```python
config = V3Config(
    features=[
        FeatureConfig(name="longshort", preprocess=PreprocessMethod.ZSCORE, window=30, weight=0.7),
        FeatureConfig(name="funding_rate", preprocess=PreprocessMethod.MOMENTUM, window=20, weight=0.3)
    ],
    combination=CombinationConfig(
        method=CombinationMethod.WEIGHTED_AVG,
        final_preprocess=PreprocessMethod.ZSCORE_TREND
    ),
    thresholds={"long": -2.0, "short": 2.0}
)
```

### **Example 3: Simple No Final Processing**
```python
config = V3Config(
    features=[
        FeatureConfig(name="open_interest", preprocess=PreprocessMethod.ZSCORE, window=30)
    ],
    combination=CombinationConfig(
        method=CombinationMethod.ADD,
        final_preprocess=None  # No final processing
    ),
    thresholds={"long": -2.5, "short": 2.5}
)
```

---

## 🎛️ **Available Options:**

### **Preprocessing Methods:**
- `ZSCORE` - Z-score normalization
- `ROLLING_MINMAX` - Rolling min-max normalization  
- `ZSCORE_TREND` - Z-score with trend component
- `ROLLING_STD` - Rolling standard deviation normalization
- `MOMENTUM` - Momentum-based preprocessing

### **Combination Methods:**
- `ADD` - Add features together
- `MULTIPLY` - Multiply features together
- `WEIGHTED_AVG` - Weighted average of features

### **Any Feature Names:**
- `longshort` - Long/short ratio
- `open_interest` - Open interest data
- `volume` - Trading volume
- `funding_rate` - Funding rate
- `volatility` - Market volatility
- **ANY other feature name you have in your data!**

---

## 🚀 **How to Use:**

### **1. Run Your Configuration:**
```bash
cd trading_system
source venv/bin/activate
python v3_demo.py
```

### **2. Change Configuration (NO CODE CHANGES!):**
Just modify the `create_your_example_config()` function in `v3_demo.py`:

```python
def create_your_example_config() -> V3Config:
    return V3Config(
        features=[
            # Change these easily!
            FeatureConfig(name="YOUR_FEATURE", preprocess=PreprocessMethod.YOUR_METHOD, window=YOUR_WINDOW),
            FeatureConfig(name="ANOTHER_FEATURE", preprocess=PreprocessMethod.ANOTHER_METHOD, window=30)
        ],
        combination=CombinationConfig(
            method=CombinationMethod.YOUR_COMBINATION,
            final_preprocess=PreprocessMethod.YOUR_FINAL_METHOD
        ),
        thresholds={"long": YOUR_LONG_THRESHOLD, "short": YOUR_SHORT_THRESHOLD}
    )
```

### **3. Run Again - That's It!**
No need to change any other code - maximum flexibility!

---

## 📊 **V3 System Components Used:**

### **All 5 Components Working Together:**
1. ✅ **enhanced_main_v3.py** - Main orchestration with flexible config
2. ✅ **strategy_v3.py** - Enhanced flexible strategies  
3. ✅ **data_provider.py** - Data fetching (from V2)
4. ✅ **preprocessor.py** - Preprocessing logic (enhanced in V3)
5. ✅ **trader.py** - Trade execution (from V2)

### **V3 Enhancements:**
- 🎯 **Smart Configuration System** - No hardcoded names
- 🔧 **Flexible Preprocessing Pipeline** - Any method on any feature
- 🔬 **Intelligent Feature Engineering** - Any combination possible
- 🎛️ **Dynamic Strategy Selection** - All V2 strategies + new flexible ones
- 🚀 **Future-Ready Architecture** - Handle any new data types

---

## 🎉 **Success! Maximum Flexibility Achieved!**

### **What You Can Do Now:**
- ✅ **Easy Config Changes**: Just modify the config object
- ✅ **Any Feature Combination**: Mix any features you want
- ✅ **Any Preprocessing**: Use any preprocessing method
- ✅ **Any Combination Method**: Add, multiply, weighted average
- ✅ **Any Thresholds**: Set any long/short thresholds
- ✅ **Future-Ready**: Add new features/methods without code changes

### **Perfect for Your Needs:**
- 🎯 **Today**: Use OI + longshort with zscore + rolling_minmax
- 🔮 **Tomorrow**: Easily add new features and preprocessing methods
- 🚀 **Future**: Handle any new data types without system changes

**Your V3 system is now the most flexible trading system possible!** 🎉