# Phase 2: SaaS Transformation Roadmap (REVISED)
## Estimation Platform - Based on Real User Workflow

**Last Updated:** October 1, 2025
**Key Insight:** Phase 1's 8-stage workflow had too many roadblocks. Franklin's spreadsheet shows how users actually work. Phase 2 simplifies to match their real process.

---

## What Changed and Why

### Phase 1 Problem (Too Complex)
Users abandoned the tool because of roadblocks:
- **Select Task Codes** → Users don't know task codes
- **Upload CAD Files** → Small jobs don't have CAD
- **Material List Generation** → Automated list doesn't match reality
- **Task Mapping** → Confusing, too many steps
- **Generate Estimate** → Results don't match their process
- Proposal Creation, Preview, Export → Nobody got this far

### Phase 2 Solution (Match Their Workflow)
Franklin's spreadsheet revealed the simple process users actually follow:
1. Import products from their existing system (NetSuite/QuickBooks)
2. Create bid items from RFP
3. Add materials/labor/equipment to each bid item
4. Calculate overhead and margins
5. Export proposal

**This is what "simple for layman" actually means** - match how they already work (spreadsheets), not force a new process.

---

## Revised Sprint Plan (6 Months)

### **Sprint 1-2: Bid Item Structure & CSV Import (Weeks 1-4)**

#### Goals
- Replace 8-stage workflow with simple bid item structure
- Import products from CSV (NetSuite/QuickBooks format)
- Users can create first estimate in 10 minutes

#### Tasks

**Bid Item Data Model**
- [ ] Create `BidSchedule` model (master list from RFP)
  - item_code, description, engineer_estimate, status, color_code
- [ ] Create `BidItem` model (detailed estimate per schedule item)
  - materials_total, labor_total, equipment_total, subcontractor_total
  - our_cost, margin_percent, sale_price
- [ ] Create `BidItemMaterial` model (material line items)
  - netsuite_internal_id, name, quantity, unit_cost, total_cost
- [ ] Create `BidItemLabor` model (labor line items)
  - classification, hours, rate, total
- [ ] Add to Opportunity model: has many BidSchedule items

**CSV Import**
- [ ] Build CSV import for Products (from Items42.xls format)
  - Columns: Internal ID, Name, Standard Cost
  - Map to existing Product model (internal_id, description, std_cost)
- [ ] Drag & drop upload interface
- [ ] Preview first 5 rows before importing
- [ ] Validation with clear errors
- [ ] Success summary (✓ 5,247 products imported)

**Simple Bid Creation Flow**
- [ ] "New Estimate" button → Create Opportunity
- [ ] "Add Bid Item" button → Create BidSchedule entry
- [ ] Bid Item detail page:
  - Add materials (search imported products)
  - Add labor (hours × rate)
  - Add equipment (hours × rate)
  - Add subcontractors (total cost)
- [ ] Auto-calculate totals as user types

**Color Status Tracking**
- [ ] Status dropdown per bid item:
  - 🟢 Green = Done estimating
  - 🔴 Red = Need to work on it
  - 🟡 Yellow = Need final quote
  - 🟠 Orange = Waiting on vendor
  - ⚫ Black = Not needed
- [ ] Visual status badges in list view

**Testing**
- [ ] Test with Franklin's Items42.xls (5,247 products)
- [ ] Recreate "Example 2 - Small PW Job.xlsx" in web app
- [ ] Measure time-to-first-estimate (goal: <10 min)

---

### **Sprint 3-4: Bid Summary & Overhead Calculations (Weeks 5-8)**

#### Goals
- Aggregate bid items into proposal summary
- Auto-calculate overhead (admin, PM, insurance, etc.)
- Margin adjustment per bid item or project-wide

#### Tasks

**Bid Summary Page**
- [ ] Master summary table showing all bid items
- [ ] Columns: Item Code, Description, Our Cost, Margin %, Sale Price, Engineer Estimate
- [ ] Totals row at bottom
- [ ] Color-coded status indicators

**Overhead Auto-Calculations**
- [ ] Create `OverheadItem` model (admin, PM, permits, insurance, bonding, etc.)
- [ ] Default percentages (configurable per organization later):
  - Admin: 5% of project total
  - Project Management: 8% of project total
  - Insurance: 0.5% of project total
  - Bonding: Based on project size (sliding scale)
  - Hotel/Per Diem: Days × rate
  - Mileage: Miles × $0.67
- [ ] Add overhead section to Bid Summary
- [ ] User can override any calculated value

**Margin Adjustments**
- [ ] Global margin % (applies to all bid items)
- [ ] Per-item margin override
- [ ] Show margin $ and margin % for each item
- [ ] Show total project margin

**Tax Calculations**
- [ ] Project-level tax rate setting
- [ ] Apply tax only to Materials and Equipment (not labor)
- [ ] Show Sale Price without Tax and with Tax
- [ ] Back-calculate margin excluding tax

**Quick Navigation**
- [ ] Hyperlinks from Bid Summary to each Bid Item
- [ ] "Back to Summary" button on every Bid Item page
- [ ] Breadcrumb navigation

---

### **Sprint 5-6: Prevailing Wage & Equipment Rates (Weeks 9-12)**

#### Goals
- Support public works prevailing wage requirements
- Link to live DIR wage determinations
- Equipment rental rate sheets

#### Tasks

**Prevailing Wage Tab**
- [ ] Create `WageClassification` model
  - classification, responsibilities, justification
  - base_rate, fringe_benefits, total_rate
  - dir_link (URL to DIR wage determination)
- [ ] List of labor classifications for project
- [ ] Add/edit wage rates
- [ ] Link to California DIR website
- [ ] Show which bid items use each classification

**Equipment Rental Rates**
- [ ] Create `EquipmentRate` model
  - equipment_type, hourly_rate, daily_rate, weekly_rate
  - rental_company, rate_sheet_link
- [ ] Equipment rate library
- [ ] Link to rental company rate sheets (CalRent, etc.)
- [ ] Quick add equipment to bid items

**Live Hyperlinks**
- [ ] Clickable links to external resources
- [ ] Open in new tab
- [ ] Store URL history (rates change over time)

---

### **Sprint 7-8: Document Management & RFP Reference (Weeks 13-16)**

#### Goals
- Upload and reference RFP documents
- Embed specs and drawings in bid items
- Quick reference while estimating

#### Tasks

**Document Upload**
- [ ] Upload RFP PDF
- [ ] Upload spec sheets
- [ ] Upload drawings/plans
- [ ] Tag documents by bid item

**Inline Document Viewer**
- [ ] PDF viewer embedded in bid item page
- [ ] Side-by-side: estimate form + specs
- [ ] Highlight and annotate documents
- [ ] Copy text from PDF to estimate

**Quick Reference Panel**
- [ ] Collapsible sidebar with documents
- [ ] Thumbnail previews
- [ ] Search within documents
- [ ] Pin important pages

---

### **Sprint 9-10: Multi-Tenant & Organization Settings (Weeks 17-20)**

#### Goals
- Support multiple companies/organizations
- Each org has isolated data
- Custom defaults per organization

#### Tasks

**Organization Model** (already started!)
- [ ] Create full `Organization` model (not just FK to User)
  - company_name, address, phone, logo
  - default_tax_rate, default_margin_percent
  - netsuite_account_id (for future integration)
- [ ] Migrate existing data to "Laurel AG & Water" organization
- [ ] Update ALL models with organization FK
- [ ] Middleware to filter queries by current user's org

**Organization Settings Page**
- [ ] Company info (name, address, logo)
- [ ] Default rates:
  - Tax rate (varies by state)
  - Margin percentage
  - Labor burden multiplier
  - Mileage rate
- [ ] Overhead defaults (admin %, PM %, insurance %)
- [ ] Custom bid item templates (saved for reuse)

**Team Collaboration**
- [ ] Invite team members via email
- [ ] Roles: Owner, Admin, Estimator, Viewer
- [ ] Assign bid items to team members
- [ ] Activity log (who changed what)
- [ ] Internal comments on bid items

---

### **Sprint 11-12: Stripe Payments & Go Live (Weeks 21-24)**

#### Goals
- Start collecting revenue
- Launch with beta customers
- Monitor usage and iterate

#### Tasks

**Pricing** (adjusted based on Franklin's needs)
- [ ] **Starter** - $99/month
  - 1 user, 5 active projects
  - CSV import
  - Basic overhead calculations
- [ ] **Professional** - $299/month
  - 5 users, unlimited projects
  - NetSuite export
  - Custom wage/equipment libraries
  - Priority support
- [ ] **Enterprise** - $699/month
  - Unlimited users
  - API access
  - Custom integrations
  - Dedicated account manager

**Stripe Integration**
- [ ] 14-day free trial (no credit card)
- [ ] Checkout flow
- [ ] Subscription management
- [ ] Invoice generation

**Export Functionality**
- [ ] Export Bid Summary to PDF (professional proposal)
- [ ] Export to CSV (NetSuite import format)
  - Include Internal IDs for product matching
  - Format matches Franklin's Items42.xls structure
- [ ] Email proposal to customer
- [ ] Track when customer opens proposal

**Launch Prep**
- [ ] Beta with Franklin's team (5 users)
  - Import their 5,247 products
  - Recreate 3 recent bids
  - Get feedback on workflow
- [ ] Fix top 5 pain points from beta
- [ ] Write help docs (quick start guide)
- [ ] Launch pricing page

---

## Data Model Summary

### Core Models (Keep from Phase 1)
- `Opportunity` - Top-level project
- `Customer` - Client information
- `Product` - Materials catalog
- `Task` - Labor tasks catalog
- `LabourCost` - Labor rates
- `Vendor` - Supplier information

### New Models (Phase 2)
- `BidSchedule` - Master list of bid items from RFP
- `BidItem` - Detailed estimate per schedule item
- `BidItemMaterial` - Material line items
- `BidItemLabor` - Labor line items
- `BidItemEquipment` - Equipment line items
- `OverheadItem` - Project overhead costs
- `WageClassification` - Prevailing wage rates
- `EquipmentRate` - Equipment rental rates
- `Organization` - Multi-tenant company model

### Removed Models
- `SelectTaskCode` - Not needed (users add items directly)
- `Document` uploads tied to stages - Simplified to general file uploads
- Complex 8-stage workflow models - Replaced with simple bid items

---

## User Experience: Before & After

### Phase 1 (Too Complex)
1. Login
2. Create Opportunity
3. Select Task Codes ❌ **Roadblock**: Don't know task codes
4. Upload CAD File ❌ **Roadblock**: Don't have CAD for small jobs
5. Review Material List ❌ **Roadblock**: Automated list is wrong
6. Map Tasks to Materials ❌ **Roadblock**: Too confusing
7. Generate Estimate ❌ **Roadblock**: Results don't match expectations
8. (Users quit before this) Create Proposal
9. Preview Proposal
10. Export PDF

**Result:** Nobody completed an estimate.

### Phase 2 (Matches Real Workflow)
1. Login
2. "New Estimate" → Enter project name, customer
3. "Import Products" → Drag & drop Items42.xls ✓ **Fast**
4. "Add Bid Items" → Enter line items from RFP ✓ **Familiar**
5. For each bid item:
   - Search products, add quantities ✓ **Simple**
   - Add labor hours × rate ✓ **Like Excel**
   - Add equipment hours × rate ✓ **Easy**
6. View Bid Summary → Adjust margins ✓ **Control**
7. "Export Proposal" → PDF + CSV for NetSuite ✓ **Done**

**Time:** 20 minutes for first estimate (goal: <10 min with practice)

**Result:** Users actually complete estimates.

---

## Why This Works

### 1. **Matches Existing Workflow**
Franklin's spreadsheet evolved over years to match how his team works. We're digitizing that, not forcing a new process.

### 2. **No Learning Curve**
If you can use Excel, you can use this. Same concepts (rows, columns, formulas), better UI.

### 3. **Import Existing Data**
Users have products in NetSuite/QuickBooks. Let them import it, don't make them re-enter.

### 4. **Fast Time-to-Value**
10 minutes to first estimate, not 2 hours learning a complex workflow.

### 5. **Flexible, Not Rigid**
8-stage workflow forced everyone through the same steps. Bid items let users work in any order.

### 6. **Export to Existing Systems**
They already use NetSuite. Export to CSV format they can import. Don't try to replace NetSuite.

---

## Success Metrics (6-Month Targets)

### Product Metrics
- **Franklin's team completes 10 estimates** in first month (validation)
- **5 new beta customers** (Laurel's competitors in ag/public works)
- **Average time-to-first-estimate:** <15 minutes
- **Completion rate:** >80% (users who start an estimate finish it)

### Revenue Metrics (Conservative)
- 5 beta customers × $299/month = $1,495 MRR
- Goal: 20 paying customers by month 6 = $5,980 MRR

### Usage Metrics
- **Products imported per org:** 1,000-10,000 (validated by Franklin's 5,247)
- **Bid items per estimate:** 10-50 (validated by Franklin's examples)
- **CSV exports per month:** 20+ (sign they're using it for real bids)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Franklin's workflow doesn't generalize | Test with 2 other contractors in beta |
| NetSuite export format breaks | Get sample export file from Franklin, validate structure |
| Overhead calculations too complex | Start with simple % defaults, add complexity later |
| Users want Excel anyway | Make export to Excel perfect, become "Excel enhancer" |
| Multi-tenant isolation issues | Add organization_id filter in middleware (already started) |

---

## Immediate Next Steps (This Week)

1. **Create BidSchedule, BidItem, BidItemMaterial models**
2. **Build CSV import for Products** (test with Items42.xls)
3. **Simple bid item detail page** (add materials, calculate totals)
4. **Show Franklin a demo** (even if rough) to validate approach
5. **Get his feedback** on what's missing

---

## Bottom Line

**Phase 1 taught us:** Complex workflows fail. Users quit.

**Franklin taught us:** Match their existing spreadsheet process.

**Phase 2 delivers:** Spreadsheet workflow, but multi-tenant SaaS with exports.

**Result:** A tool people will actually use and pay for.
