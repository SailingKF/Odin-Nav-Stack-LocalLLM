# PROJECT.md

## Project Name
**Odin Tour Guide Local**

A location-triggered, local-LLM-assisted tour guide layer built on top of Odin-Nav-Stack.

---

## Project Goal

Build a tour-guide application layer that:
- triggers explanation automatically when the robot reaches configured map locations
- uses a curated content library as the knowledge source
- uses a local LLM to produce natural spoken explanations and answer follow-up questions
- exposes an Android-friendly control/debug UI
- records session data and video for offline analysis
- can be developed on a laptop first, validated in simulation, and later deployed on embedded platforms such as Orin NX

---

## Why This Project Exists

The original navigation stack provides a strong base for robot motion, navigation, and perception experiments.  
This project adds a product-oriented application layer for **tourism, guided interaction, and location-aware narration**.

The key value is:
- no hard dependency on cloud latency
- reusable, controlled explanation content
- smoother human interaction in tourism or exhibition scenarios
- a clear path from mock development to simulation to real robot deployment

---

## Product Definition

### Core Interaction Loop
1. Select route/tour mode
2. Robot navigates toward next POI
3. When entering POI trigger radius, narration starts automatically
4. User can interrupt and ask a question
5. Local LLM answers using curated content
6. Session continues to next POI
7. Video and logs are saved for offline review

### Knowledge Strategy
- **Source of truth:** human-maintained content library
- **LLM role:** rephrase, personalize, answer, summarize
- **No uncontrolled hallucination-first design**

### Video Strategy
- **Runtime:** record only
- **Post-run:** offline analytics

---

## Target Platforms

### 1. Development Workstation
Purpose:
- fast development
- mock integration
- UI iteration
- service debugging

### 2. Simulation Environment
Purpose:
- validate POI-triggered narration with simulated pose
- validate end-to-end app behavior before hardware access
- Isaac Sim is the preferred simulation target when needed

### 3. Embedded Edge Device
Primary future target:
- **Jetson Orin NX**
Goals:
- local inference/control
- real deployment in field environments
- limited-resource optimization

### 4. Android Control Surface
Primary intended field control client:
- task control
- state monitoring
- route/POI debugging
- quick pause/resume diagnostics

---

## Current Scope

### Phase 0: Documentation and workflow foundation
- AGENT.md
- PROJECT.md
- ARCHITECTURE.md
- DEV_WORKFLOW.md
- DEPLOYMENT.md

### Phase 1: Mock-first runnable application layer
- mock pose provider
- POI manager
- tour orchestrator
- session logger

### Phase 2: Local LLM integration
- local gateway
- narration generation using content library
- Q&A support

### Phase 3: Android-friendly control UI
- route selection
- status page
- current POI / current narration
- debug controls

### Phase 4: Simulation validation
- Isaac Sim integration through pose adapters
- simulated tour runs
- session replay verification

### Phase 5: Edge deployment preparation
- Orin NX compatibility pass
- config layering
- resource-aware deployment modes

### Phase 6: Real hardware integration
- replace mock adapters with robot integrations
- audio/video/input device bindings
- field testing

---

## Functional Requirements

### Must Have
- position-triggered POI narration
- configurable POI and route content
- local LLM-based rephrasing/Q&A
- session logs
- Android-accessible control/debug UI
- future-compatible deployment design for Orin NX

### Nice to Have Later
- multilingual tour styles
- multiple tour themes
- analytics dashboard
- interest heatmaps
- visitor interaction summaries

---

## Non-Goals for Early Development
- full cloud backend dependency
- real-time video intelligence
- aggressive low-level odin-nav-stack refactor
- direct platform entanglement inside business logic

---

## Risks

### Technical Risks
- over-coupling product logic to ROS or a specific simulator
- introducing dependencies too heavy for Orin NX
- making UI desktop-first and later hard to adapt to Android
- letting LLM output drift from curated content

### Process Risks
- making prompts too large and causing uncontrolled repo-wide changes
- trying to build simulation and hardware integration before mock flow is stable
- skipping documentation and losing project consistency

---

## Success Criteria

This project is succeeding when:
1. a developer can run a simulated or mock tour loop on a laptop
2. a route with multiple POIs can trigger narration automatically
3. the UI can control and inspect the session from an Android-friendly interface
4. the system architecture can transition to Orin NX without redesigning the core application logic
5. the same core tour logic works across dev, sim, and edge with adapter changes only
