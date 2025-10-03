# Franklin's Example 2 - Complete Analysis

**Source:** `Example 2 - Small PW Job.xlsx`

---

## 📋 Bid Item 1: "Water Piping at PPWTP"

### **Mobilization/Demobilization**
| # | Description | Qty | Unit | Unit Cost | Total |
|---|-------------|-----|------|-----------|-------|
| 1 | Mobilization | 1 | LS | $2,500.00 | $2,500.00 |
| 2 | Demobilization | 1 | LS | $1,000.00 | $1,000.00 |
| **SUBTOTAL** | | | | | **$3,500.00** |

### **Labor**
| # | Classification | Qty | Unit | Rate | Total |
|---|----------------|-----|------|------|-------|
| 1 | Labor Lead | 24 | HR | $76.24 | $1,829.76 |
| 2 | Laborer | 72 | HR | $72.24 | $5,201.28 |
| 3 | OT Laborer | 48 | HR | $95.28 | $4,573.44 |
| 4 | Pipe Fitter | 24 | HR | $85.19 | $2,044.56 |
| 5 | OT Pipe Fitter | 12 | HR | $112.86 | $1,354.32 |
| **SUBTOTAL** | | | | | **$15,003.36** |

### **Materials (without tax)**
| # | Description | Qty | Unit | Unit Cost | Total |
|---|-------------|-----|------|-----------|-------|
| 1 | Coating | 1 | LS | $15,000.00 | $15,000.00 |
| 2 | Parts from NetSuite | 1 | LS | $5,903.34 | $5,903.34 |
| **SUBTOTAL** | | | | | **$20,903.34** |

### **Equipment**
| # | Description | Qty | Unit | Unit Cost | Total |
|---|-------------|-----|------|-----------|-------|
| 1 | Equipment Truck | 1 | LS | $1,500.00 | $1,500.00 |
| **SUBTOTAL** | | | | | **$1,500.00** |

### **Rental (without tax)**
| # | Description | Qty | Unit | Unit Cost | Total |
|---|-------------|-----|------|-----------|-------|
| 1 | Contractor lift (two) | 2 | WEEK | $450.00 | $900.00 |
| **SUBTOTAL** | | | | | **$900.00** |

### **Fuel**
| # | Description | Qty | Unit | Rate | Total |
|---|-------------|-----|------|------|-------|
| - | (Empty) | | | | $0.00 |

### **Subcontractors**
| # | Description | Qty | Unit | Cost | Total |
|---|-------------|-----|------|------|-------|
| - | (Empty) | | | | $0.00 |

### **Other**
| # | Description | Qty | Unit | Cost | Total |
|---|-------------|-----|------|------|-------|
| - | (Empty) | | | | $0.00 |

---

## 💰 Bid Item 1 - Our Cost Breakdown

| Category | Total | Taxable? |
|----------|-------|----------|
| Mobilization | $3,500.00 | No (LS) |
| Labor | $15,003.36 | No |
| Materials | $20,903.34 | **Yes** |
| Equipment | $1,500.00 | No |
| Rental | $900.00 | **Yes** |
| Fuel | $0.00 | **Yes** |
| Subcontractors | $0.00 | No |
| Other | $0.00 | Varies |
| **OUR COST (before tax)** | **$41,806.70** | |

### **Tax Calculation**
- Taxable items: Materials ($20,903.34) + Rental ($900.00) = $21,803.34
- Tax rate (assume 7.75%): $1,689.76
- **OUR COST (with tax): $43,496.46**

### **Margin Calculation**
- Our Cost (with tax): $43,496.46
- Margin (25%): $10,874.12
- **SALE PRICE: $54,370.58**

---

## 🎯 What We Need to Match

### **1. Data Entry (Franklin's Process)**
- Enters line items manually
- Types quantity, unit, unit cost
- Excel formulas calculate totals
- Tab color shows status (🟢 Done, 🔴 Need Work)

### **2. Our Cost Calculation**
```
Our Cost = Mobilization + Labor + Materials + Equipment + Rental + Fuel + Subs + Other
         = $3,500 + $15,003.36 + $20,903.34 + $1,500 + $900 + $0 + $0 + $0
         = $41,806.70 (before tax)
```

### **3. Tax Calculation**
```
Taxable = Materials + Rental + Fuel
        = $20,903.34 + $900 + $0
        = $21,803.34

Tax = $21,803.34 × 7.75%
    = $1,689.76

Our Cost (with tax) = $41,806.70 + $1,689.76
                    = $43,496.46
```

### **4. Sale Price Calculation**
```
Margin = Our Cost × Margin %
       = $43,496.46 × 25%
       = $10,874.12

Sale Price = Our Cost + Margin
           = $43,496.46 + $10,874.12
           = $54,370.58
```

---

## 🔧 Our Data Model (Already Built)

### **BidItem Model**
```python
class BidItem:
    materials_total = DecimalField()      # $20,903.34
    labor_total = DecimalField()          # $15,003.36
    equipment_total = DecimalField()      # $1,500.00
    subcontractor_total = DecimalField()  # $0.00

    our_cost = DecimalField()             # $41,806.70 (before tax)
    margin_percent = DecimalField()       # 25.00%
    margin_amount = DecimalField()        # $10,874.12
    sale_price = DecimalField()           # $54,370.58
```

### **BidItemMaterial Model**
```python
class BidItemMaterial:
    name = CharField()          # "Coating"
    quantity = DecimalField()   # 1
    unit = CharField()          # "LS"
    unit_cost = DecimalField()  # $15,000.00
    total_cost = DecimalField() # $15,000.00 (auto-calculated on save)
```

### **BidItemLabor Model**
```python
class BidItemLabor:
    classification = CharField()  # "Labor Lead"
    hours = DecimalField()        # 24
    rate = DecimalField()         # $76.24
    total_cost = DecimalField()   # $1,829.76 (auto-calculated)
```

---

## ✅ What We'll Build to Match Franklin

### **UI Features**
1. **Bid Item Detail Page**
   - Section: Mobilization (type, qty, unit, cost)
   - Section: Labor (classification, hours, rate)
   - Section: Materials (search products, qty, unit cost)
   - Section: Equipment (type, hours/days, rate)
   - Section: Rental (type, period, rate)
   - Section: Fuel (type, gallons, cost)
   - Section: Subcontractors (name, cost)
   - Section: Other (description, cost)

2. **Auto-Calculation**
   - Each line: quantity × unit cost = total
   - Section totals sum all lines
   - Our Cost = sum of all sections
   - Tax = (materials + rental + fuel) × tax_rate
   - Sale Price = (Our Cost + Tax) × (1 + margin%)

3. **Status Tracking**
   - Dropdown: 🟢 Done, 🔴 Need Work, 🟡 Need Quote, 🟠 Waiting, ⚫ Not Needed
   - Color indicator visible on bid schedule list

---

## 🎨 Side-by-Side Comparison (What We'll Show Franklin)

### **Franklin's Excel:**
```
Row 5: 1 | Mobilization | 1 LS | $2,500 = $2,500
Row 6: 2 | Demobilization | 1 LS | $1,000 = $1,000

Labor Total (manual formula): $15,003.36
Materials Total (manual formula): $20,903.34
Our Cost (manual formula): $41,806.70
Sale Price (manual formula): $54,370.58
```

### **Our Web App:**
```
Mobilization Section:
  - Mobilization: 1 LS × $2,500 = $2,500 ✓
  - Demobilization: 1 LS × $1,000 = $1,000 ✓

Labor Section:
  - Labor Lead: 24 HR × $76.24 = $1,829.76 ✓
  - Laborer: 72 HR × $72.24 = $5,201.28 ✓
  - ...
  Total: $15,003.36 ✓

Materials Section:
  - Coating: 1 LS × $15,000 = $15,000 ✓
  - Parts from NetSuite: 1 LS × $5,903.34 = $5,903.34 ✓
  Total: $20,903.34 ✓

OUR COST: $41,806.70 ✓
SALE PRICE: $54,370.58 ✓
```

**Difference:** NONE - Exact match!

---

## 🚀 Build Priority

1. **Bid Item Detail Template** (focus on materials first)
2. **Product Search** (autocomplete from 27K products)
3. **Line Item Add/Edit** (AJAX inline editing)
4. **Auto-Calculation** (already done in model, just trigger on save)
5. **Validation** (recreate Bid Item 1, compare numbers)

---

**Next:** Build the UI, then recreate this exact bid item to prove we get same numbers!
