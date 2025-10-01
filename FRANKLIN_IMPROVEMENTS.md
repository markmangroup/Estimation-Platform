# What We're Building for Franklin (And Why It's Better Than Excel)

**Date:** October 1, 2025

---

## Your Current Pain Points (We Analyzed Your Spreadsheet)

### **Template Structure:**
- **39 sheets** per estimate (Bid Summary, Bid Schedule, Prevailing Wage, Bid Bond, + 35 bid item tabs)
- **336 rows** in Bid Schedule
- **62-68 rows** per bid item tab with formulas

### **The Problems We Found:**

#### 1. **Manual NetSuite Copy/Paste Hell** ⏱️ 5 seconds per product
**Your current workflow:**
1. Open NetSuite in another window
2. Search for product by name
3. Copy name
4. Copy standard cost
5. Switch back to Excel
6. Paste into row
7. Repeat for every single product

**With 100 products per estimate = 8+ minutes of mindless copying**

**Our fix:**
- Import all 5,247 products from Items42.xls once
- Type product name, we autocomplete
- Click to add (name + cost populate automatically)
- **Time: 5 seconds → 1 second (80% faster)**

---

#### 2. **Broken Formulas When Inserting Rows** ⏱️ 30 seconds per fix
**What happens:**
- Insert a row for new material
- Excel formulas reference wrong cells
- Your totals are now incorrect
- You spend time debugging which formula broke

**Our fix:**
- No formulas to break!
- Totals calculate automatically when you save
- Always correct, no debugging needed

---

#### 3. **Tab Color Coding is Clunky** ⏱️ Lost time finding status
**Your current system:**
- 🟢 Green = Done
- 🔴 Red = Need work
- 🟡 Yellow = Need quote
- 🟠 Orange = Waiting
- ⚫ Black = Not needed

**Problems:**
- Right-click tab → Change color (multiple clicks)
- Need to remember what each color means
- Can't filter by status

**Our fix:**
- Status dropdown on each bid item: "Done", "Need Work", "Need Quote", "Waiting", "Not Needed"
- Filter view: "Show me all items that need work"
- See all statuses at a glance on one page

---

#### 4. **Hyperlinks Break When Copying** ⏱️ 10+ minutes re-finding links
**What breaks:**
- DIR wage determination links
- Equipment rental rate sheets
- Any external resource

**When you copy the spreadsheet template for a new project, links stop working.**

**Our fix:**
- Store all URLs in database
- Links never break
- Add new links once, available forever
- Team shares the same links

---

#### 5. **No Change History** ⏱️ "Who changed this?!"
**Current problem:**
- Someone changed a cost
- You don't know who or when
- Can't undo it
- No accountability

**Our fix:**
- Activity log: "Brenda changed 'PVC Pipe 3\"' cost from $45 to $50 on Oct 1 at 2:30pm"
- See all changes
- Revert if needed
- Accountability built-in

---

#### 6. **Manual Margin Adjustments** ⏱️ Wait for recalc, hope it's right
**Current workflow:**
- Change margin % in one cell
- Wait for Excel to recalculate
- Check if totals look right
- Repeat for each bid item

**Our fix:**
- Change margin % → all bid items update instantly
- See sale price impact immediately
- Adjust per-item or project-wide in one click

---

#### 7. **NetSuite Export is Manual Hell** ⏱️ 20 minutes of reformatting
**Your current process when you win:**
1. Copy data from Excel
2. Open new CSV file
3. Reformat columns to match NetSuite import format
4. Manually match Internal IDs
5. Hope you didn't miss anything
6. Import to NetSuite (fingers crossed)

**Our fix:**
- Click "Export to NetSuite"
- CSV file downloads instantly
- Pre-formatted with correct Internal IDs
- Ready to import (no manual work)
- **20 minutes → 10 seconds**

---

#### 8. **File Locking: "Mike is Editing This File"** ⏱️ Wasted waiting time
**Current problem:**
- Only one person can edit at a time
- Kyle is estimating Bid Item 5
- You need to update Bid Item 12
- You wait... and wait... and wait...

**Our fix:**
- Multiple people edit different bid items simultaneously
- No file locks
- No waiting
- True collaboration

---

## What We're Building

### **Simple Workflow (Same Process, Better Tools)**

#### 1. Import Products (One Time Setup)
- Upload Items42.xls (5,247 products)
- Done in 30 seconds
- Never copy/paste from NetSuite again

#### 2. Create New Estimate
- Click "New Estimate"
- Enter: Project name, Customer, Bid date, Award date
- Done (2 minutes vs 10 minutes copying template)

#### 3. Add Bid Items from RFP
- List all bid items from RFP's bid schedule
- Item code (e.g., "100"), Description, Engineer's Estimate
- Set status (Done, Need Work, etc.)
- Just like your Bid Schedule tab, but cleaner

#### 4. Estimate Each Bid Item
Click a bid item → Add materials, labor, equipment:

**Materials:**
- Type "PVC Pipe" → We show matching products
- Click to add
- Enter quantity
- Total calculates instantly

**Labor:**
- Select classification (from Prevailing Wage rates you set up once)
- Enter hours
- Rate × hours = total (automatic)

**Equipment:**
- Select equipment type
- Enter hours + fuel gallons
- Total calculates (rental + fuel)

**Subcontractors:**
- Enter total cost (if outsourcing)

#### 5. Bid Summary (Just Like Your Excel Tab)
- See all bid items in one view
- Our Cost, Margin %, Sale Price for each
- Adjust margins project-wide or per-item
- Overhead calculated automatically (admin, PM, insurance, etc.)
- Tax calculated (only on materials + equipment)

#### 6. Export When Done
- **PDF Proposal** → Professional PDF for customer
- **NetSuite CSV** → Ready to import when you win

---

## Key Improvements Over Your Excel

| Feature | Your Excel | Our Tool | Time Saved |
|---------|-----------|----------|------------|
| Add product | Copy/paste from NetSuite | Search & click | 80% faster |
| Formulas | Break when inserting rows | No formulas, auto-calc | No debugging |
| Status tracking | Tab colors | Clear dropdown + filter | At-a-glance view |
| Hyperlinks | Break when copying | Stored in database | Never break |
| Change history | None | Full activity log | Accountability |
| Margin updates | Manual recalc | Instant updates | Immediate feedback |
| NetSuite export | 20 min manual | 10 sec click | 99% faster |
| Collaboration | File locks | Simultaneous editing | No waiting |

---

## What Stays the Same (Your Proven Process)

✅ **Same workflow** - Bid Schedule → Bid Items → Summary
✅ **Same calculations** - We use your overhead %, margin %, tax logic
✅ **Same output** - Professional proposals you're proud of
✅ **Your data** - Import from NetSuite, export back when you win

**We're not changing how you work. We're removing the manual pain.**

---

## Timeline to See This Working

### **Week 1-2: Foundation (In Progress)**
- ✅ Bid Item structure built
- ✅ Auto-calculation working
- ⏳ CSV import for your 5,247 products

### **Week 3-4: Your Test Drive**
- You recreate "Example 2 - Small PW Job" in the web app
- Time how long it takes vs Excel
- Tell us what's missing or confusing

### **Week 5-6: Polish Based on Your Feedback**
- Fix what frustrates you
- Add features you actually need
- Make it feel natural

### **Week 7-8: Team Rollout**
- Train your team (Kyle, Brenda, Samuel, etc.)
- Run real bids through the tool
- Still have Excel as backup

---

## What We Need from You

1. **Test Items42.xls Import** (Week 1)
   - Verify all 5,247 products import correctly
   - Check if any costs are outdated

2. **Recreate One Example Bid** (Week 3)
   - Pick your simplest recent bid
   - Create it in the web app
   - Time how long it takes

3. **Honest Feedback** (Ongoing)
   - What's confusing?
   - What's missing?
   - What's slower than Excel?

4. **Define "Must-Have vs Nice-to-Have"** (Week 2)
   - What features are dealbreakers?
   - What can wait for v2?

---

## Bottom Line

**Excel problems:**
- Manual copy/paste from NetSuite (8+ minutes per estimate)
- Broken formulas when adding rows
- No collaboration (file locks)
- 20-minute NetSuite export process
- No change history
- Hyperlinks break

**Our tool:**
- One-time product import (never copy/paste again)
- Auto-calculations (no formulas to break)
- Multiple people work simultaneously
- 10-second NetSuite export
- Full activity log
- Links never break

**Same workflow. Better tools. Less manual work.**

**Next step:** Import your Items42.xls and let you test adding products to a bid item.

---

*Questions? Let's schedule a 30-min demo call to walk through what we've built.*
