import json
import os
import uuid

topics = [
    "DSA", "OOP", "DBMS", "OS & Networks", 
    "System Design", "Behavioral", "Domain Specific"
]

questions = []

templates = {
    "DSA": [
        ("Reverse a Linked List", "How do you reverse a singly linked list in-place?", ["Linked Lists", "Pointers"], "Iterate through the list, changing the next pointer of each node to point to the previous node.", "def reverseList(head): ..."),
        ("Detect Cycle", "How to detect a cycle in a linked list?", ["Linked Lists", "Floyd's Algorithm"], "Use two pointers, slow and fast.", "def hasCycle(head): ..."),
        ("Binary Search", "Implement binary search on a sorted array.", ["Arrays", "Search"], "Find middle, if target < mid search left, else search right.", "def search(nums, target): ..."),
        ("Merge K Sorted Lists", "Merge k sorted linked lists into one sorted list.", ["Heaps", "Divide and Conquer"], "Use a min-heap to keep track of the smallest current element.", "def mergeKLists(lists): ..."),
        ("LRU Cache", "Design an LRU Cache with O(1) get and put.", ["Design", "Hash Map", "Doubly Linked List"], "Use a dict for fast lookup and a doubly linked list for fast removal.", "class LRUCache: ..."),
        ("Valid Parentheses", "Check if a string containing parentheses '()[]{{}}' is valid.", ["Stacks"], "Use a stack to push opening brackets and pop/check closing brackets.", "def isValid(s): ..."),
        ("Two Sum", "Find two numbers in an array that add up to a target sum.", ["Arrays", "Hash Map"], "Store seen numbers in a hash map mapping value to index.", "def twoSum(nums, target): ..."),
        ("Longest Substring Without Repeats", "Find the length of the longest substring without repeating characters.", ["Sliding Window", "Hash Set"], "Use a sliding window and a set/dict to track seen characters.", "def lengthOfLongestSubstring(s): ...")
    ],
    "OOP": [
        ("Polymorphism", "Explain Polymorphism in object-oriented programming with an example.", ["Polymorphism", "OOP Concepts"], "The ability of different objects to respond to the same method call in their own specific way.", None),
        ("Inheritance vs Composition", "What is the difference between inheritance and composition? When would you use each?", ["Design Principles", "Inheritance", "Composition"], "Inheritance represents an IS-A relationship, whereas Composition represents a HAS-A relationship. Favor composition for flexibility.", None),
        ("Encapsulation", "What is encapsulation and how does it promote maintainability?", ["Encapsulation", "OOP Concepts"], "Bundling data and methods that operate on that data within a single unit/class while restricting direct access to internal state.", None),
        ("Abstract Class vs Interface", "What are the key differences between an Abstract Class and an Interface?", ["Interfaces", "Abstract Classes"], "Abstract classes can have instance state and default method bodies; interfaces define contracts.", None),
        ("SOLID Principles", "Explain the SOLID principles of object-oriented software design.", ["Design Principles", "SOLID"], "Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.", None),
        ("Singleton Pattern", "Explain the Singleton design pattern, its implementation, and potential drawbacks.", ["Design Patterns", "Singleton"], "Ensures a class has only one instance. Drawbacks include hidden global dependencies and tight coupling.", None),
        ("Factory Pattern", "Explain the Factory Method Pattern and how it promotes loose coupling.", ["Design Patterns", "Factory"], "Delegates object instantiation to subclasses without specifying exact concrete classes.", None),
        ("Method Overloading vs Overriding", "Explain the difference between method overloading and method overriding.", ["Polymorphism", "OOP Concepts"], "Overloading is compile-time polymorphism (same method, different parameters). Overriding is runtime polymorphism (redefining a superclass method).", None)
    ],
    "DBMS": [
        ("ACID Properties", "What are the ACID properties in database transactions?", ["ACID", "Transactions"], "Atomicity (all-or-nothing), Consistency (valid state transitions), Isolation (concurrent transaction safety), Durability (persisted changes).", None),
        ("Database Indexing", "How do B-Tree database indexes improve query performance?", ["Indexing", "B-Trees", "Performance"], "Indexes create balanced search trees on indexed columns, reducing query time complexity from O(N) sequential scan to O(log N).", None),
        ("Database Normalization", "What is database normalization and why is 3NF commonly targeted?", ["Normalization", "Schema Design"], "Organizing columns and tables to minimize data redundancy and insertion/deletion anomalies.", None),
        ("SQL vs NoSQL", "Compare relational (SQL) databases with document-based (NoSQL) databases.", ["SQL", "NoSQL", "Architecture"], "SQL provides structured schema and ACID transactions; NoSQL provides flexible schema and horizontal scaling.", None),
        ("SQL Joins", "Explain the differences between INNER, LEFT, RIGHT, and FULL OUTER JOINs.", ["SQL", "Joins"], "INNER returns matching rows in both tables; LEFT returns all rows from left table plus matched right rows; FULL returns all rows when there is a match in either.", "SELECT * FROM users u LEFT JOIN orders o ON u.id = o.user_id;"),
        ("Database Transactions", "What is a database transaction and how do savepoints work?", ["Transactions", "Concurrency"], "A logical unit of work executed atomically. Savepoints allow rolling back to intermediate states.", None),
        ("Deadlocks in Databases", "What causes database deadlocks and how can database systems prevent or detect them?", ["Concurrency", "Deadlocks", "Locking"], "Occurs when two transactions hold locks wanted by the other. Systems detect via wait-for graphs or prevent via lock ordering.", None),
        ("CAP Theorem", "Explain the CAP theorem in distributed database design.", ["Distributed Systems", "CAP Theorem"], "A distributed data store can simultaneously provide at most two of: Consistency, Availability, and Partition Tolerance.", None)
    ],
    "OS & Networks": [
        ("Process vs Thread", "What is the key difference between a process and a thread?", ["Process Management", "Threads"], "A process has its own isolated memory space. Threads share memory space within the parent process.", None),
        ("Virtual Memory & Paging", "Explain how virtual memory and page tables work in modern operating systems.", ["Virtual Memory", "Paging", "Memory Management"], "Translates virtual addresses to physical RAM addresses via page tables and translation lookaside buffers (TLB).", None),
        ("Mutex vs Semaphore", "Compare Mutex and Semaphore synchronization primitives.", ["Concurrency", "Mutex", "Semaphore"], "A Mutex is a locking mechanism (owned by one thread). A Semaphore is a signaling mechanism using a counter.", None),
        ("OSI Model Layers", "Describe the 7 layers of the OSI networking model.", ["OSI Model", "Networking"], "Physical, Data Link, Network, Transport, Session, Presentation, Application.", None),
        ("TCP vs UDP", "Compare TCP and UDP transport layer protocols.", ["TCP", "UDP", "Networking"], "TCP is connection-oriented, reliable, ordered. UDP is connectionless, unreliable, low-latency.", None),
        ("DNS Resolution", "Explain step-by-step how DNS resolution converts a domain name to an IP address.", ["DNS", "Networking"], "Browser cache -> OS cache -> Recursive Resolver -> Root Server -> TLD Server -> Authoritative Nameserver.", None),
        ("TCP 3-Way Handshake", "Explain the TCP three-way handshake process.", ["TCP", "Handshake", "Networking"], "SYN (Client to Server) -> SYN-ACK (Server to Client) -> ACK (Client to Server).", None),
        ("System Calls & Context Switching", "What occurs during a CPU context switch initiated by a system call?", ["Context Switch", "Kernel", "CPU Scheduling"], "CPU switches from user mode to kernel mode, saves register state, loads the target process/thread register state.", None)
    ],
    "System Design": [
        ("URL Shortener", "How would you design a scalable URL shortener service like Bitly?", ["System Design", "Hashing", "Database"], "Use base62 encoding of auto-incrementing IDs or MD5 hashes, a key-value store (Redis/Cassandra) for fast redirects, and a load balancer.", None),
        ("Load Balancing", "Explain load balancing algorithms (Round Robin, Least Connections, Consistent Hashing).", ["Load Balancing", "Scalability"], "Round Robin rotates sequentially; Least Connections routes to least busy node; Consistent Hashing minimizes key remapping on cluster changes.", None),
        ("Caching Strategies", "Compare Cache-Aside, Write-Through, Write-Behind, and Refresh-Ahead caching patterns.", ["Caching", "Performance"], "Cache-Aside reads cache first then DB; Write-Through updates cache and DB synchronously; Write-Behind updates DB asynchronously.", None),
        ("Database Sharding", "What is database sharding and how do you handle cross-shard queries?", ["Sharding", "Scalability", "Database"], "Horizontal partitioning of database rows across multiple machines by shard key.", None),
        ("Message Queues & Pub/Sub", "When and why would you use an event-driven architecture with Kafka or RabbitMQ?", ["Message Queues", "Asynchronous", "Event-Driven"], "Decouples producers and consumers, buffers high throughput traffic spikes, enables async event processing.", None),
        ("API Rate Limiting", "Design an API rate limiter using the Token Bucket or Sliding Window algorithm.", ["Rate Limiting", "API Design", "Redis"], "Token bucket adds tokens at fixed rate; requests consume tokens. Sliding window log counts timestamps in Redis.", None),
        ("Microservices Architecture", "Discuss the trade-offs of Microservices vs Monolithic architecture.", ["Microservices", "Architecture"], "Microservices allow independent deployment and scaling but introduce distributed complexity, network latency, and eventual consistency.", None),
        ("Distributed Tracing", "How do you trace user requests across dozens of microservices?", ["Observability", "Distributed Systems"], "Inject trace and span IDs in HTTP headers (OpenTelemetry/Jaeger) to track call trees across services.", None)
    ],
    "Behavioral": [
        ("Technical Conflict", "Describe a technical disagreement you had with a teammate and how you resolved it.", ["Conflict Resolution", "Teamwork"], "STAR method: Situation, Task, Action (listened, gathered data, benchmarked), Result (reached consensus).", None),
        ("Handling Failure", "Tell me about a time a project or deployment failed. What did you learn?", ["Self-Awareness", "Post-Mortem"], "STAR method: Owned responsibility, ran post-mortem, introduced automated tests/monitoring to prevent recurrence.", None),
        ("Technical Leadership", "Describe a situation where you took initiative to improve a system or engineering process.", ["Leadership", "Initiative"], "Identified bottleneck/tech debt, proposed solution to team, built prototype, led adoption.", None),
        ("Tight Deadlines & Scope", "How do you handle a situation where a feature deadline cannot be met with full scope?", ["Time Management", "Prioritization"], "Communicated early with stakeholders, identified MVP/core path, deferred non-critical subfeatures.", None),
        ("Receiving Critical Feedback", "Describe a time you received constructive feedback on your code or performance.", ["Growth Mindset", "Feedback"], "Listened without defensiveness, applied suggestions, followed up to verify improvement.", None),
        ("Disagree and Commit", "Tell me about a time you disagreed with an architectural decision made by leadership.", ["Communication", "Professionalism"], "Presented evidence-based alternative, accepted final decision gracefully, committed 100% to execution.", None),
        ("Mentoring Teammates", "How have you helped onboard or mentor junior engineers on your team?", ["Mentorship", "Team Building"], "Pair programming, thorough code reviews, creating documentation and onboarding guides.", None),
        ("Learning New Tech", "Tell me about a time you had to learn an unfamiliar technology under time pressure.", ["Adaptability", "Learning"], "Broke down requirements, built small proof-of-concept, leveraged documentation, delivered on time.", None)
    ],
    "Domain Specific": [
        ("REST vs GraphQL", "Compare RESTful API design with GraphQL for frontend-backend communication.", ["API Design", "REST", "GraphQL"], "REST uses fixed endpoints per resource; GraphQL uses single endpoint allowing clients to request exact fields.", None),
        ("Docker Containerization", "How does Docker container isolation differ from full virtual machines?", ["DevOps", "Docker", "Containers"], "Containers share the host OS kernel and isolate user space using cgroups/namespaces; VMs run full guest OS on hypervisor.", None),
        ("CI/CD Pipeline", "What are the core stages of a production CI/CD pipeline?", ["DevOps", "CI/CD"], "Lint -> Unit Tests -> Build Artifact -> Integration Tests -> Staging Deploy -> Production Deploy.", None),
        ("Web Security (OWASP Top 10)", "Explain XSS, CSRF, and SQL Injection vulnerabilities and their preventions.", ["Security", "OWASP", "Web"], "XSS: sanitize input/escape output; CSRF: use anti-CSRF tokens/SameSite cookies; SQLi: use parameterized queries.", None),
        ("OAuth2 & JWT", "How does OAuth2 authentication flow work with JWT access tokens?", ["Security", "OAuth2", "JWT"], "Client authenticates with Auth Provider, receives signed JWT containing user claims/exp, passes Bearer token to API.", None),
        ("React Rendering & Virtual DOM", "Explain how React's Virtual DOM and reconciliation algorithm optimize rendering.", ["Frontend", "React", "Virtual DOM"], "React keeps virtual UI tree, computes diff (reconciliation) on state change, applies minimal DOM mutations.", None),
        ("Async/Await & Event Loop", "Explain the event loop and non-blocking I/O model in Node.js or Python asyncio.", ["Async", "Event Loop", "Runtimes"], "Single thread runs event loop checking task queue/callbacks; I/O operations delegated to OS kernel/worker threads.", None),
        ("Kubernetes Pods & Services", "What is a Kubernetes Pod and how does a Service route traffic to Pods?", ["Kubernetes", "DevOps", "Cloud"], "Pod is smallest deployable unit (1+ containers). Service uses label selectors to load balance traffic across Pod IPs.", None)
    ]
}

for topic, q_list in templates.items():
    for i, q in enumerate(q_list):
        diff = 1 + (i % 10)  # 1-10 scale
        
        q_obj = {
            "id": str(uuid.uuid4()),
            "title": q[0],
            "question": q[1],
            "topic": topic,
            "difficulty": diff,
            "concepts": q[2],
            "tags": [topic.lower().replace(" ", "_").replace("&", "and"), "interview"],
            "expected_answer": q[3],
            "sample_code": q[4],
            "language": "python" if q[4] else None,
            "hints": ["Consider the core principles of " + q[0]]
        }
        questions.append(q_obj)

os.makedirs("data/questions", exist_ok=True)
with open("data/questions/seed_questions.json", "w") as f:
    json.dump(questions, f, indent=2)

print(f"Generated {len(questions)} questions across {len(templates)} topics in data/questions/seed_questions.json")
