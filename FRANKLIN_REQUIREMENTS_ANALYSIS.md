# Franklin's Requirements vs Phase 2 SaaS Roadmap Analysis

**Date:** October 1, 2025
**Client:** Franklin Gaudi - Laurel Ag & Water
**Context:** Phase 1 tool was built, but client wants Excel-based workflow digitized instead

---

## Franklin's Core Request

> "Using the attached spreadsheets as examples, make a web-based version that allows us to link our NetSuite database of parts/materials so that it populates the part name and cost into our template as we use it."

**Translation:** He wants his Excel spreadsheet workflow (Public Works Template v7) replicated in a web app, NOT the 8-stage estimation tool we built.

---

## Key Franklin Requirements

### 1. **NetSuite Integration (CRITICAL)**
- Import materials from NetSuite with Name + Standard Cost
- Export proposal back to NetSuite when they win the bid
- **Current tool:** No NetSuite integration at all
- **Phase 2 plan:** QuickBooks integration in Sprint 11-12 (Sprints 9-10 in new roadmap)

### 2. **Bid Item Tabs with Color Coding**
- Green = Done estimating
- Red = Need to work on it
- Yellow/Orange = Need final quote
- Black = Not needed
- **Current tool:** No bid item concept, no color status tracking
- **Phase 2 plan:** Status badges mentioned but not this granular

### 3. **Multi-Tab Structure**
- Bid Summary tab (master calculations, margin adjustments)
- Prevailing Wage tab (labor classifications, DIR links)
- Equipment Rental Rates tab (live hyperlinks)
- Multiple Bid Item tabs (one per line item in RFP)
- **Current tool:** Single opportunity with 8-stage workflow
- **Phase 2 plan:** Doesn't account for this

### 4. **Bid Schedule List**
- List of bid items from RFP
- Each gets its own tab
- Tabs are auto-named from Bid Schedule
- **Current tool:** No concept of multiple bid items
- **Phase 2 plan:** Single opportunity focus

### 5. **Side Calculations & Excel Functions**
- Need space for ad-hoc calculations on each tab
- Users want basic Excel formula capabilities
- **Current tool:** No calculation workspace
- **Phase 2 plan:** Not mentioned

### 6. **RFP Reference Documents**
- Copy/paste specs and drawings into bid tabs
- Quick reference while estimating
- **Current tool:** File uploads exist but no inline reference
- **Phase 2 plan:** Photo galleries mentioned but not document embedding

### 7. **Hyperlinks to Live Data**
- DIR wage determinations (live updates)
- Equipment rental rate sheets
- **Current tool:** Static data only
- **Phase 2 plan:** Not mentioned

### 8. **Quick Navigation**
- Hyperlinks from Bid Summary to each Bid Item tab
- "Back to Bid Summary" links on every tab
- **Current tool:** Linear 8-stage workflow
- **Phase 2 plan:** Not mentioned

### 9. **Overhead Calculations**
- Admin, PM, permits, mileage, hotels, per diem, insurance, bonding
- All calculated as % of project cost
- Tax rate configurable per project
- **Current tool:** Basic margin/tax fields
- **Phase 2 plan:** Default margin/tax in templates

### 10. **Engineer Estimates & Dates**
- Record engineer's estimate (from RFP)
- Track bid date, award date, estimated dates
- Notes about date certainty
- **Current tool:** Basic opportunity dates
- **Phase 2 plan:** Not specifically addressed

---

## Critical Disconnect

### What We Built (Phase 1)
8-stage linear workflow:
1. Select Task Codes
2. Upload CAD Files
3. Material List Generation
4. Task Mapping
5. Generate Estimate
6. Proposal Creation
7. Proposal Preview
8. Final Document Export

**Problem:** This assumes irrigation/ag projects with CAD files and standardized tasks. Franklin's public works bids are RFP-based with custom bid schedules.

### What Franklin Actually Needs
Multi-tab spreadsheet digitization:
1. Import NetSuite materials
2. Create bid items from RFP schedule
3. Estimate each bid item separately (materials, labor, equipment, subs)
4. Aggregate to Bid Summary with overhead
5. Adjust margins per bid item
6. Export back to NetSuite when won

---

## Items42.xls - NetSuite Product Catalog

**File size:** 8.1 MB
**Purpose:** Complete product catalog with Internal ID, Name, Standard Cost
**Usage:** Search by Name, populate Standard Cost, need Internal ID for NetSuite import

**This is CRITICAL** - without NetSuite integration, the tool is useless to Franklin.

---

## Gap Analysis: Phase 2 Roadmap vs Franklin's Needs

| Franklin Need | Phase 2 Coverage | Priority | Gap Severity |
|--------------|------------------|----------|--------------|
| NetSuite integration | Sprint 11-12 (QuickBooks planned) | CRITICAL | High |
| Bid item multi-tab structure | Not mentioned | CRITICAL | High |
| Color-coded status tracking | Basic status badges | High | Medium |
| Side calculation workspace | Not mentioned | High | High |
| Live hyperlinks (DIR, rates) | Not mentioned | Medium | Medium |
| RFP document embedding | Photo galleries only | Medium | Medium |
| Excel-like formula engine | Not mentioned | Medium | High |
| Overhead auto-calculations | Basic defaults | Medium | Medium |
| Export back to NetSuite | Not mentioned | CRITICAL | High |

---

## Strategic Decision Required

### Option A: Pivot to Franklin's Workflow
**Pros:**
- Franklin is a paying client with clear requirements
- Public works bidding is a different (larger?) market than ag irrigation
- His spreadsheet process is mature and battle-tested
- NetSuite integration opens B2B opportunities

**Cons:**
- Completely different from Phase 2 SaaS roadmap
- Multi-tab spreadsheet paradigm is complex
- Excel formula engine is hard to build
- Might not fit "simple for layman" SaaS vision

### Option B: Build Hybrid System
**Pros:**
- Support both workflows (irrigation templates + public works bid items)
- Broader market appeal
- Leverage template work we just did

**Cons:**
- Double the complexity
- Diluted focus
- Longer time to market
- Confusing value proposition

### Option C: Stay Course on Phase 2 (Ignore Franklin)
**Pros:**
- Focus on original SaaS vision
- Templates + mobile + simple onboarding
- Broader SMB market vs enterprise

**Cons:**
- Lose Franklin as reference client
- Existing Phase 1 tool doesn't fit his needs
- Wasted Phase 1 development investment

---

## Recommendations

### Immediate Action
1. **Call Franklin** - Explain that Phase 1 tool was built for ag/irrigation workflow, his needs are different
2. **Demo current tool** - Show him templates, see if any pieces fit
3. **Get budget commitment** - "tight scope" and "get a win" suggests budget constraints

### If Pursuing Franklin's Workflow
**Sprint 1-2 (Revised):**
- Build Bid Item concept (not templates)
- NetSuite CSV import (use Items42.xls format)
- Bid Schedule master list with color status
- Basic bid item detail page (materials, labor, equipment)

**Sprint 3-4:**
- Bid Summary aggregation
- Overhead calculations
- Margin adjustments per bid item
- Export to CSV for NetSuite import

**Sprint 5-6:**
- Multi-tab navigation
- Inline calculations (basic formula engine)
- Document embedding (specs, drawings)

This is a COMPLETELY different product than our Phase 2 roadmap.

### If Staying Course on Phase 2
**Tell Franklin:**
> "The tool we built is designed for ag irrigation projects with CAD files. Your public works bidding workflow is different - you need a digital version of your Excel spreadsheet. That's a separate project with different requirements (NetSuite integration, bid item structure, overhead calculations). Let's scope that separately as a Phase 1B project before we move to Phase 2 SaaS features."

---

## Data Model Implications

### If we support Franklin's workflow:

```python
class BidSchedule(BaseModel):
    """Master list of bid items from RFP"""
    opportunity = models.ForeignKey(Opportunity)
    item_code = models.CharField(max_length=50)  # e.g., "100", "200"
    description = models.TextField()
    engineer_estimate = models.DecimalField()
    status = models.CharField(max_length=20)  # draft, estimating, quoted, complete
    color_code = models.CharField(max_length=20)  # green, red, yellow, orange, black
    sequence = models.IntegerField()

class BidItem(BaseModel):
    """Individual bid item with materials/labor/equipment"""
    bid_schedule = models.ForeignKey(BidSchedule)

    # Materials (from NetSuite)
    materials_total = models.DecimalField()

    # Labor (from Prevailing Wage tab)
    labor_hours = models.DecimalField()
    labor_total = models.DecimalField()

    # Equipment
    equipment_hours = models.DecimalField()
    equipment_total = models.DecimalField()

    # Subcontractors
    subcontractor_total = models.DecimalField()

    # Calculations
    our_cost = models.DecimalField()
    margin_percent = models.DecimalField()
    sale_price = models.DecimalField()

class BidItemMaterial(BaseModel):
    """Material line item within bid item"""
    bid_item = models.ForeignKey(BidItem)
    netsuite_internal_id = models.IntegerField()  # Link to NetSuite
    name = models.CharField(max_length=255)
    quantity = models.DecimalField()
    unit_cost = models.DecimalField()  # From NetSuite
    total_cost = models.DecimalField()
```

This is very different from our Template models.

---

## Bottom Line

**Franklin wants a completely different product** than what our Phase 2 SaaS roadmap delivers.

His needs:
- NetSuite-integrated bid management
- Multi-tab RFP response tool
- Public works overhead calculations
- Export to NetSuite on win

Our Phase 2 plan:
- Template-based quick estimates
- Mobile-first UX
- Multi-tenant SaaS
- Simple onboarding for SMBs

**These are two different products serving two different workflows.**

Decision needed: Which product do we build?
