# Nielsen Norman Group — Research Findings Summary

**Sources Consulted**: 4 NNg articles
**Date Accessed**: March 27, 2026
**Tier**: Tier 2 (Gold-standard UX research organization)

---

## Article 1: 8 Design Guidelines for Complex Applications
**Author**: Kate Kaplan | **Published**: November 8, 2020
**URL**: https://www.nngroup.com/articles/complex-application-design/

### Definition of Complex Application
"Any application supporting the broad, unstructured goals or nonlinear workflows of highly trained users in specialized domains." Complex apps frequently:
- Require substantial domain knowledge
- Support underlying data sets and enable advanced sensemaking or data analysis

### The 8 Guidelines

1. **Support Learning by Doing** (Paradox of the Active User)
   - Users prefer to start using immediately, undeterred by complexity
   - Risky to rely solely on trial-and-error for mission-critical domains
   - Support exploration without experimentation resulting in loss of work
   - Example: Dashboard construction where results are visible as built

2. **Help Users Adopt More Efficient Methods**
   - Embed in-context learning cues for accelerators
   - Tooltips that suggest faster methods as users hover over toolbar items

3. **Provide Flexible and Fluid Pathways**
   - Multiple routes to the same data/action
   - Not just one way to accomplish a task

4. **Help Users Track Actions and Thought Processes**
   - Enable users to keep a record of actions during work
   - User-entered notes and comments on data sets and charts
   - Reduce breaks in workflow

5. **Coordinate Transition Among Multiple Tools and Workspaces**
   - Integration between different views and tools
   - Copy visuals as images for external use (Power BI example)

6. **Reduce Clutter Without Reducing Capability** ← KEY FOR US
   - Complex apps accommodate broad range of uses → powerful but cluttered
   - Must support both novice and expert users simultaneously
   - Expert users need advanced features that infrequent users rarely access
   - **Staged disclosure**: Show options only when relevant to current task
   - Reduce visual clutter within interface WITHOUT removing capability
   - Show features to user only when they are relevant to task at hand

7. **Ease Transition Between Primary and Secondary Information** ← KEY FOR US
   - Not all information can be displayed at once
   - Some information must be deferred to secondary levels
   - Secondary information is often necessary to contextualize primary-level decisions
   - Allow users to access supplemental information without leaving primary environment
   - Example: Hover to view more precise detail about a specific chart point

8. **Make Important Information Visually Salient** ← KEY FOR US
   - Complex-app tasks require high degree of visual search
   - Users must locate and distinguish relevant data across tabular views in huge tables
   - System alerts must draw attention to relevant parts of the interface
   - Viewing data visualizations has significant visual-search component
   - Competing information and elements can hinder these tasks
   - Make critical elements stand out from surrounding elements
   - Standing out does NOT always mean adding (bold, heavier font weight)
   - **Removing competing elements can be equally effective** at making important information salient

---

## Article 2: Dashboards — Making Charts and Graphs Easier to Understand
**Author**: Page Laubheimer | **Published**: June 18, 2017
**URL**: https://www.nngroup.com/articles/dashboards-preattentive/

### Dashboard Definition
"Data visualizations, presented in a single-page view that imparts at-a-glance information on which users can act quickly."

### Operational vs. Analytical Dashboards

**Operational Dashboards:**
- Provide information quickly for immediate decisions and time-sensitive tasks
- Examples: server availability, patient vitals, customer service calls, flight traffic
- Present continuously updating data
- Help identify unacceptable deviations in parameters
- Visualize available resources

**Analytical Dashboards:**
- Help users identify need for deeper analysis
- Updated less frequently (e.g., once a day)
- Don't have same time sensitivity as operational
- Demand thoughtful analysis

### Preattentive Processing

Preattentive attributes ranked by accuracy for quantitative comparison:
1. **2D Position** (most accurate) — Where a data point sits on a chart
2. **Length** (very accurate) — Bar height/width → easy to compare
3. **Angle** (less accurate) — Pie chart slices → harder to judge
4. **Area** (least accurate) — Bubble sizes → very hard to compare accurately

**Critical Finding on Color:**
- Color is a powerful preattentive attribute for NOTICING (red dot in blue dots)
- People do NOT perceive colors as being in a particular order
- **Color should NOT be used to communicate quantitative values or magnitude**
- Use color for categorical distinction only (compliant/non-compliant, not "how compliant")
- 4.5% of general population has some form of color blindness
- 8% of men vs 0.5% of women affected
- Numbers vary by ethnicity

### Linear vs. Area-Based Graphs
- 2D position and length are the two attributes that best support quick data comparisons
- Bar charts are effective because we pre-attentively process bar length
- Bar charts allow easy comparison of values, especially when ordered (ascending/descending)
- Reference: Cleveland and McGill 1985 paper on data visualization accuracy

---

## Article 3: Data Tables — Four Major User Tasks
**Author**: Page Laubheimer | **Published**: April 3, 2022
**URL**: https://www.nngroup.com/articles/data-tables/

### Summary
"Table design should support four common user tasks: find records that fit specific criteria, compare data, view/edit/add a single row's data, and take actions on records."

### Tables vs. Cards/Modules
- Tables are "not usually winners of a UI beauty contest"
- They are "utilitarian" parts of design
- But tables have functional advantages over cards, dashboards, and other visualizations

### Primary Advantages of Tables
1. **Scalability**: Easy to increase rows AND columns as dataset changes
2. **Support for comparison tasks**: Adjacent data points easy to compare without working memory load (no need to remember or look back and forth)

### Power User Eye-Tracking Pattern
From Finviz stock screener study:
- User moved between table data and filters above
- Scanned first column, second column, then **skipped to 4th and 6th columns**
- Power users don't read tables sequentially — they jump to relevant columns
- This means: put the most important columns (severity, status) early, but users will adapt

---

## Article 4: Progressive Disclosure
**Author**: Jakob Nielsen | **Published**: December 3, 2006
**URL**: https://www.nngroup.com/articles/progressive-disclosure/

### Definition
"Progressive disclosure defers advanced or rarely used features to a secondary screen, making applications easier to learn and less error-prone."

### The Designer's Dilemma
- Users want power features to handle all special needs
- Users also want simplicity and ease of use
- Progressive disclosure solves this by showing common features upfront and advanced features on demand

### Key Principle
Show the most common options first, defer advanced options. This reduces:
- Learning time (fewer features to understand initially)
- Error rate (fewer options = fewer wrong choices)
- Cognitive load (less to process at once)

### Application to Our Dashboard
- Dashboard summary = primary disclosure (always visible)
- Detail panels = secondary disclosure (on click/hover)
- Advanced filters = tertiary disclosure (behind "+ Add filter")
- Configuration/settings = deepest level (behind gear icon)
