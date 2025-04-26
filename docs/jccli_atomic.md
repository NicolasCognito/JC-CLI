# Atomic Experiments for JC-CLI Development

## Concept Overview

Atomic experiments are isolated, minimal implementations that test a single architectural principle or component. They provide a systematic approach to developing complex scripts like JC-CLI game logic by breaking down the architecture into independently verifiable components.

## Core Characteristics

An atomic experiment should be:

1. **Focused** - Tests exactly one architectural principle
2. **Minimal** - Contains only what's needed to verify the principle
3. **Self-contained** - Functions independently of other components
4. **Verifiable** - Success criteria are clear and testable
5. **Reusable** - Patterns can be incorporated into the final implementation
6. **Disposable** - Can be discarded after the principle is validated

## Why This Approach Works for JC-CLI

JC-CLI's architecture is based on several core principles that must work together seamlessly:

- **Two Realms Separation** (Infrastructure vs. Logic)
- **Network-first Execution Model**
- **Deterministic Command Processing**
- **Radical Minimalism**
- **Transparent State**

Testing these principles together immediately would create a complex system with numerous potential failure points. Atomic experiments allow us to verify each principle independently before integration.

## Methodology

### 1. Principle Identification

Select a single principle from the JC-CLI architecture to test. For example:
- Command distribution over network
- File-based state persistence
- Command execution via subprocesses
- Rule application after command execution

### 2. Experiment Design

Create a minimal design that tests only this principle:
- Define clear success criteria
- Identify the smallest possible implementation
- Remove anything not directly related to the principle
- Document assumptions and constraints

### 3. Implementation

Build the experiment following these guidelines:
- Use the simplest possible code
- Avoid premature optimization
- Focus on clarity over elegance
- Document key design decisions

### 4. Verification

Test the experiment against its success criteria:
- Does it verify the principle in question?
- Does it demonstrate the expected behavior?
- Are there any edge cases that should be addressed?

### 5. Documentation

Document the experiment and its findings:
- What was tested
- How it was implemented
- What was learned
- What patterns should be carried forward

## Completed Experiments

1. **Basic Command Execution**
   - **Principle**: Subprocess-based command execution with file-based state
   - **Implementation**: Simple orchestrator and command script
   - **Finding**: Validated the separation between infrastructure and logic realms

2. **Thin Server**
   - **Principle**: Network-first execution model with deterministic command ordering
   - **Implementation**: Coordinator server with multiple isolated clients
   - **Finding**: Confirmed commands can traverse a network and be ordered deterministically

## Potential Future Experiments

1. **Rule Loop**
   - Test automatic effects triggered by rule code after command execution
   - Ensure deterministic outcomes across multiple clients

2. **World Snapshot**
   - Test serialization and deserialization of world state
   - Ensure identical rendering across clients

3. **Replay System**
   - Test replaying commands from initial state
   - Verify deterministic recreation of final state

4. **View Separation**
   - Test rendering different views of the same world state
   - Validate information hiding for player vs. admin views

## Evaluating Success

An atomic experiment is successful when:

1. It clearly demonstrates the principle being tested
2. It produces consistent, deterministic results
3. It reveals patterns that can be used in the final system
4. It documents essential knowledge about the principle
5. It identifies constraints or limitations that must be addressed

## Integration Path

After conducting multiple atomic experiments:

1. Identify common patterns across experiments
2. Create a unified architecture that preserves the verified principles
3. Implement the complete system using the validated patterns
4. Test the integrated system against the original architectural goals
5. Document the final design and its relationship to the atomic experiments

## Conclusion

The atomic experiment approach enables rapid, confident development of complex systems by breaking them into verifiable components. For JC-CLI, this methodology allows us to test each architectural principle independently before integration, ensuring a solid foundation and clear understanding of each component's behavior.