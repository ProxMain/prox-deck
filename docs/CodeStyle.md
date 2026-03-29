\# Agent.md



\## Purpose



This document defines the architectural, structural, and review rules for this project.



It serves two purposes:



1\. As an implementation guide for all generated and edited code.

2\. As a review standard to critically assess whether code remains maintainable, minimal, explicit, and aligned with the intended architecture.



This document is intentionally feature-agnostic. It does not describe product behavior, screens, workflows, or business features. It defines how code must be designed, organized, and reviewed.



\---



\## Core Intent



The codebase must remain:



\- explicit

\- modular

\- predictable

\- readable

\- testable

\- minimal

\- resistant to architectural drift



All code must prefer clarity over cleverness.



The project must not evolve into a script-like, framework-entangled, or convenience-driven codebase. Every addition must preserve structure, responsibility boundaries, and long-term maintainability.



\---



\## Architectural Philosophy



The architecture must be built around clear responsibilities and strict boundaries.



The codebase must follow a layered design with strong separation of concerns. The exact module names may evolve, but the responsibilities must remain stable.



\### Expected responsibility separation



\- \*\*Presentation\*\*

&#x20; - UI rendering

&#x20; - user interaction

&#x20; - event forwarding

&#x20; - framework-specific view behavior



\- \*\*Application\*\*

&#x20; - orchestration of use cases

&#x20; - coordination between services, repositories, and policies

&#x20; - application flow control

&#x20; - no direct framework-heavy UI implementation



\- \*\*Domain\*\*

&#x20; - business rules

&#x20; - models

&#x20; - value objects

&#x20; - contracts

&#x20; - policies

&#x20; - domain exceptions

&#x20; - no framework coupling



\- \*\*Infrastructure\*\*

&#x20; - persistence

&#x20; - operating system integration

&#x20; - external services

&#x20; - platform APIs

&#x20; - concrete implementations of contracts



\- \*\*Bootstrap / Composition Root\*\*

&#x20; - dependency wiring

&#x20; - object construction

&#x20; - startup configuration

&#x20; - no business logic



\---



\## Non-Negotiable Design Principles



\### SOLID



All code must follow SOLID principles.



\#### Single Responsibility Principle

A class must have one clear responsibility and one clear reason to change.



A class must not combine:

\- UI rendering

\- persistence

\- orchestration

\- system integration

\- business rules

\- configuration handling



\#### Open/Closed Principle

The code should be open for extension and closed for modification.



Prefer adding new implementations over rewriting existing stable behavior.



\#### Liskov Substitution Principle

Implementations of a contract must behave consistently and predictably.



No implementation may silently change expectations around return values, side effects, or error behavior.



\#### Interface Segregation Principle

Interfaces must remain small and focused.



Avoid broad contracts that group unrelated concerns.



\#### Dependency Inversion Principle

Higher-level components must depend on abstractions, not concrete implementations.



Use contracts/interfaces for repositories, providers, services where appropriate, and extensibility points.



\---



\### POLA



The Principle of Least Astonishment applies everywhere.



Code must behave as another experienced developer would reasonably expect.



This means:

\- names must match behavior

\- methods must avoid hidden side effects

\- getters must not mutate state

\- loaders must not persist data

\- finders must not silently fall back unless explicitly documented

\- control flow must be easy to follow

\- object lifecycle must be explicit



Avoid surprising shortcuts, magic behavior, or implicit conventions unless they are extremely well justified.



\---



\### DRY



Do not duplicate knowledge.



However, DRY must not be used as an excuse for premature abstraction.



Apply DRY when:

\- the same rule is implemented in multiple places

\- the same transformation logic is repeated

\- the same orchestration pattern is repeated with identical intent



Do not abstract merely because two blocks look similar.



Prefer a small amount of duplication over a harmful abstraction.



\---



\### KISS



Keep solutions simple and explicit.



Prefer:

\- direct constructor injection

\- straightforward composition

\- explicit registrations

\- predictable control flow

\- simple factories when needed

\- minimal indirection



Avoid:

\- unnecessary abstraction layers

\- reflection-heavy registration

\- dynamic import systems without a real need

\- service locator patterns

\- hidden global state

\- over-engineered generic solutions



\---



\### Separation of Concerns



Each layer and component type must remain within its responsibility.



Do not place:

\- business logic in views

\- persistence in controllers

\- framework logic in domain models

\- application orchestration inside repositories

\- UI behavior inside policies

\- OS integration in domain objects



\---



\### Tell, Don’t Ask



Behavior should live near the object responsible for it.



Prefer explicit domain or service actions over procedural orchestration spread across multiple consumers.



Avoid pulling internal state out of objects merely to make decisions externally when that decision belongs inside the responsible abstraction.



\---



\### YAGNI



Do not introduce speculative architecture.



Do not build for imagined future requirements without a present need.



Avoid:

\- extension points with no consumer

\- abstract base hierarchies with one implementation and no near-term variation

\- plugin systems without actual plugin use

\- configuration complexity without active use cases

\- generic managers that exist only for future possibility



Architecture must support growth, but must not assume growth that does not yet exist.



\---



\## Preferred Component Types



These terms must be used carefully and consistently.



\### Models

Models represent domain concepts or application state structures.



Models must not become passive bags of unrelated data with framework leakage.



\### Value Objects

Value objects represent immutable conceptual values and must remain explicit and small.



\### Repositories

Repositories are responsible for retrieving and persisting data.



Repositories must not contain UI logic, orchestration logic, or unrelated domain rules.



\### Services

Services contain focused logic that does not naturally belong inside an entity/value object.



A service must not become a dumping ground.



A service must have one coherent responsibility.



\### Controllers

Controllers translate presentation events into application actions.



Controllers coordinate but should remain thin.



Controllers must not absorb business rules, persistence details, or platform-specific low-level behavior unless that is explicitly their responsibility.



\### Policies

Policies contain decision rules.



Policies should answer questions like:

\- whether something is allowed

\- which option should be chosen under defined rules

\- what behavior applies in a specific state or context



Policies must remain deterministic and focused.



\### Managers

Use the term `Manager` sparingly.



A manager is only acceptable when it coordinates multiple lower-level collaborators around one clearly bounded responsibility.



A manager must not become a god object.



\### Contracts / Interfaces

Contracts are required where they improve clarity, substitution, testing, or boundary enforcement.



Use contracts especially for:

\- repositories

\- providers

\- infrastructure boundaries

\- extension points

\- policy abstractions where multiple implementations are expected



Do not introduce interfaces for every class by default.



Interfaces must exist for a reason, not ceremony.



\---



\## Dependency Rules



The codebase must enforce directional dependencies.



\### Allowed directions



\- Presentation may depend on Application

\- Application may depend on Domain

\- Infrastructure may depend on Domain and Application contracts

\- Bootstrap may depend on everything for wiring purposes



\### Forbidden directions



\- Domain must not depend on Presentation

\- Domain must not depend on Infrastructure

\- Domain must not depend on framework UI code

\- Repositories must not depend on Views

\- Policies must not depend on widgets or UI classes

\- Presentation must not directly own persistence logic

\- Infrastructure must not dictate domain behavior



\---



\## Framework Boundary Rule



Framework-specific code must be isolated.



For a desktop UI project, framework code belongs in the presentation layer and selected infrastructure integrations.



Framework concepts must not leak into:

\- domain models

\- policies

\- value objects

\- repository contracts

\- core application rules



The framework is an implementation detail around the core, not the core itself.



\---



\## Composition Root Rule



All dependency wiring must be explicit and centralized.



A composition root or bootstrap layer must:

\- construct concrete implementations

\- bind contracts to implementations

\- create controllers/services/repositories

\- initialize application startup



Dependency wiring must not be scattered across views, utilities, or random module entry points.



Avoid hidden runtime dependency creation deep in the codebase.



\---



\## Naming Rules



Names must be literal and responsibility-driven.



A class name must clearly describe what it does.



Good names:

\- `SettingsRepository`

\- `WindowPlacementService`

\- `ScreenSelectionPolicy`

\- `DashboardController`



Bad names:

\- `Helper`

\- `Util`

\- `CommonManager`

\- `SystemHandler`

\- `DataProcessor`

\- `BaseThing`



Avoid vague names.



Avoid names that hide multiple responsibilities.



\---



\## File and Module Design Rules



Files must remain small and coherent.



A file must not contain multiple unrelated abstractions.



A module must have a clear purpose.



Avoid:

\- giant mixed-purpose modules

\- deep circular imports

\- “misc” folders

\- “shared” folders that become dumping grounds

\- catch-all utility files



Shared code must only exist when it is truly shared and responsibility-consistent.



\---



\## State Management Rules



State must have an explicit owner.



Every mutable state should answer:

\- who owns it

\- who may modify it

\- through which path it changes

\- what guarantees exist around consistency



Avoid ad hoc mutable shared state.



Avoid hidden singleton-style state unless deliberately designed and documented.



\---



\## Error Handling Rules



Errors must be explicit, intentional, and consistent.



Do not silently swallow exceptions.



Do not hide broken behavior behind fallback logic unless that fallback is an intentional rule.



Use domain-specific or application-specific exceptions where meaningful.



User-facing error handling and technical diagnostics must remain separated.



\---



\## Testing Philosophy



Code must be designed to be testable.



The architecture must support isolated testing of:

\- policies

\- services

\- domain models

\- repositories

\- controllers where practical



Tests must validate behavior, not implementation trivia.



A lack of testability is often a design smell and must be treated as such.



\---



\## Anti-Bloat Rules



Every new class, method, abstraction, or layer must justify its existence.



Before introducing any abstraction, ask:

\- does this solve a current problem

\- does this improve clarity

\- does this reduce coupling

\- does this improve testability

\- does this prevent duplication of knowledge

\- does this preserve boundaries



If the answer is no, do not introduce it.



Prefer fewer, stronger abstractions over many weak ones.



\---



\## Explicitly Forbidden Patterns



The following are not allowed unless a clear architectural exception is documented:



\- business logic inside UI views

\- repositories called directly from widgets/views

\- god services

\- god managers

\- mixed-responsibility utility classes

\- hidden global state

\- service locator patterns

\- implicit dependency creation throughout the codebase

\- framework leakage into domain models

\- broad “base” classes without a strong reason

\- speculative abstractions

\- premature generic frameworks inside the project

\- catch-all helpers

\- silent fallback behavior without explicit policy

\- magic registration through filesystem scanning unless justified

\- convenience shortcuts that bypass architecture



\---



\## Review Mandate



All code review must evaluate both correctness and architectural integrity.



A review must actively challenge:

\- bloated code

\- unnecessary indirection

\- weak naming

\- mixed responsibilities

\- hidden coupling

\- speculative abstractions

\- framework leakage

\- unclear ownership

\- oversized classes

\- oversized files

\- convenience-driven shortcuts



The review must not only ask whether code works.



The review must ask whether the code:

\- belongs in the right layer

\- has the right responsibility

\- can be understood quickly

\- preserves architectural boundaries

\- introduces unnecessary complexity

\- creates future maintenance cost



\---



\## Required Review Lens



Every review must explicitly consider:



1\. \*\*Responsibility\*\*

&#x20;  - Does each class have one clear purpose?



2\. \*\*Boundary discipline\*\*

&#x20;  - Are layer boundaries preserved?



3\. \*\*Abstraction quality\*\*

&#x20;  - Is the abstraction necessary and justified?



4\. \*\*Readability\*\*

&#x20;  - Is the code explicit and unsurprising?



5\. \*\*Bloat detection\*\*

&#x20;  - Can this be made smaller, clearer, or more focused?



6\. \*\*Testability\*\*

&#x20;  - Is the design test-friendly?



7\. \*\*Dependency direction\*\*

&#x20;  - Are dependencies pointing the right way?



8\. \*\*Framework containment\*\*

&#x20;  - Is framework code isolated where it should be?



9\. \*\*Naming quality\*\*

&#x20;  - Do names accurately describe intent and responsibility?



10\. \*\*Future maintenance\*\*

&#x20;   - Will this remain understandable and safe to extend?



\---



\## Review Behavior Standard



Reviews must be critical, not permissive.



The reviewer must default to protecting clarity, simplicity, and architectural integrity.



The reviewer must challenge:

\- over-design

\- under-design

\- bloated methods

\- bloated classes

\- fake abstractions

\- accidental complexity

\- architecture bypasses



Approval must not be based solely on working behavior.



Approval requires structural quality.



\---



\## Code Generation Standard



When generating code for this project:



\- preserve strict responsibility boundaries

\- prefer explicitness over shortcuts

\- avoid unnecessary classes

\- avoid unnecessary inheritance

\- use contracts where they add meaningful value

\- keep framework code isolated

\- keep orchestration out of views

\- keep domain logic out of infrastructure

\- keep files focused

\- keep methods small and intention-revealing



Generated code must resemble production architecture, not prototype code.



\---



\## Default Decision Rule



When multiple valid solutions exist, prefer the one that is:



1\. simpler

2\. clearer

3\. more explicit

4\. easier to test

5\. easier to replace

6\. more aligned with responsibility boundaries



Do not prefer the most clever solution.



Prefer the most maintainable one.



\---



\## Final Rule



This document is not optional guidance.



It is the governing standard for both implementation and review.



If code conflicts with this document, the code must be reconsidered before acceptance.

