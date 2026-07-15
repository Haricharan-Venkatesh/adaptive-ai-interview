import json
import os
import uuid

topics = [
    "DSA", "OOP", "DBMS", "Operating Systems", 
    "Computer Networks", "System Design", "Behavioral"
]

questions = []
id_counter = 1

# Generate 8 questions per topic to hit 56 total
templates = {
    "DSA": [
        ("Reverse a Linked List", "How do you reverse a singly linked list?", ["Linked Lists", "Pointers"], "Iterate through the list, changing the next pointer of each node to point to the previous node.", "def reverseList(head): ..."),
        ("Detect Cycle", "How to detect a cycle in a linked list?", ["Linked Lists", "Floyd's Algorithm"], "Use two pointers, slow and fast.", "def hasCycle(head): ..."),
        ("Binary Search", "Implement binary search.", ["Arrays", "Search"], "Find middle, if target < mid search left, else search right.", "def search(nums, target): ..."),
        ("Merge K Sorted Lists", "Merge k sorted linked lists.", ["Heaps", "Divide and Conquer"], "Use a min-heap to keep track of the smallest current element.", "def mergeKLists(lists): ..."),
        ("LRU Cache", "Design an LRU Cache.", ["Design", "Hash Map", "Doubly Linked List"], "Use a dict for fast lookup and a doubly linked list for fast removal.", "class LRUCache: ..."),
        ("Valid Parentheses", "Check if string of parentheses is valid.", ["Stacks"], "Use a stack to push opening brackets and pop/check closing brackets.", "def isValid(s): ..."),
        ("Two Sum", "Find two numbers that add up to target.", ["Arrays", "Hash Map"], "Store seen numbers in a hash map.", "def twoSum(nums, target): ..."),
        ("Longest Substring", "Find longest substring without repeating characters.", ["Sliding Window"], "Use a sliding window and a set/dict to track seen characters.", "def lengthOfLongestSubstring(s): ...")
    ],
    "OOP": [
        ("Polymorphism", "Explain Polymorphism in OOP.", ["Concepts"], "The ability of different objects to respond to the same method call in their own way.", None),
        ("Inheritance vs Composition", "Difference between inheritance and composition?", ["Design Principles"], "Inheritance is an IS-A relationship, Composition is a HAS-A relationship.", None),
        ("Encapsulation", "What is encapsulation?", ["Concepts"], "Bundling data and methods that operate on that data within a single unit or class, restricting direct access.", None),
        ("Abstract Class vs Interface", "Difference between Abstract Class and Interface.", ["Concepts", "Java/C#"], "Abstract classes can have state and implemented methods, interfaces generally define a contract.", None),
        ("SOLID Principles", "What are the SOLID principles?", ["Design Principles"], "Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.", None),
        ("Singleton Pattern", "Explain the Singleton pattern and its drawbacks.", ["Design Patterns"], "Ensures a class has only one instance. Drawbacks include hidden dependencies and difficulty in testing.", None),
        ("Factory Pattern", "What is the Factory Method Pattern?", ["Design Patterns"], "Creates objects without specifying the exact class to create.", None),
        ("Method Overloading vs Overriding", "Difference between overloading and overriding?", ["Concepts"], "Overloading is same method name with different params (compile time). Overriding is same signature in subclass (runtime).", None)
    ],
    "DBMS": [
        ("ACID Properties", "What are the ACID properties?", ["Transactions"], "Atomicity, Consistency, Isolation, Durability.", None),
        ("Indexes", "How do database indexes work?", ["Performance", "B-Trees"], "Data structures (like B-Trees) that improve speed of data retrieval at the cost of writes and space.", None),
        ("Normalization", "What is database normalization?", ["Schema Design"], "Process of organizing data to reduce redundancy and improve data integrity (1NF, 2NF, 3NF).", None),
        ("SQL vs NoSQL", "When would you choose NoSQL over SQL?", ["Architecture"], "When you need flexible schema, horizontal scaling for massive data, or document-based storage.", None),
        ("Joins", "Explain the different types of SQL JOINs.", ["SQL"], "INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN.", "SELECT * FROM A INNER JOIN B ON A.id = B.id;"),
        ("Transactions", "What is a database transaction?", ["Transactions"], "A logical unit of work that must either completely succeed or completely fail.", None),
        ("Deadlocks", "What is a deadlock and how to prevent it?", ["Concurrency"], "When two transactions wait for locks held by each other. Prevent by acquiring locks in a consistent order.", None),
        ("CAP Theorem", "Explain the CAP theorem.", ["Distributed Systems"], "A distributed data store can only simultaneously provide two of three: Consistency, Availability, Partition tolerance.", None)
    ],
    "Operating Systems": [
        ("Process vs Thread", "What is the difference between a process and a thread?", ["Concepts"], "A process is an executing program with its own memory space. A thread is a lightweight unit of execution within a process sharing the same memory.", None),
        ("Virtual Memory", "Explain virtual memory.", ["Memory Management"], "A memory management technique that gives the illusion of a very large main memory by paging to disk.", None),
        ("Mutex vs Semaphore", "Difference between a mutex and a semaphore.", ["Concurrency"], "Mutex provides mutual exclusion (locking). Semaphore is a signaling mechanism (counting).", None),
        ("Deadlock Conditions", "What are the four Coffman conditions for deadlock?", ["Concurrency"], "Mutual exclusion, Hold and wait, No preemption, Circular wait.", None),
        ("Context Switching", "What happens during a context switch?", ["CPU Scheduling"], "Saving the state of the old process/thread and loading the state of the new one.", None),
        ("Paging vs Segmentation", "Difference between paging and segmentation?", ["Memory Management"], "Paging divides memory into fixed-size blocks. Segmentation divides memory into variable-sized logical blocks.", None),
        ("System Calls", "What is a system call?", ["Concepts"], "The programmatic way a program requests a service from the kernel.", None),
        ("Thrashing", "What is thrashing?", ["Memory Management"], "When a system spends more time paging data between memory and disk than executing instructions.", None)
    ],
    "Computer Networks": [
        ("OSI Model", "What are the 7 layers of the OSI model?", ["Concepts"], "Physical, Data Link, Network, Transport, Session, Presentation, Application.", None),
        ("TCP vs UDP", "Differences between TCP and UDP?", ["Transport Layer"], "TCP is connection-oriented, reliable, ordered. UDP is connectionless, unreliable, fast.", None),
        ("DNS", "How does DNS work?", ["Application Layer"], "Translates human-readable domain names to IP addresses via a hierarchical lookup.", None),
        ("HTTP vs HTTPS", "Difference between HTTP and HTTPS.", ["Application Layer", "Security"], "HTTPS uses TLS/SSL to encrypt HTTP requests and responses.", None),
        ("Three-way Handshake", "Explain the TCP three-way handshake.", ["Transport Layer"], "SYN, SYN-ACK, ACK.", None),
        ("IP Addresses", "Difference between IPv4 and IPv6?", ["Network Layer"], "IPv4 uses 32-bit addresses, IPv6 uses 128-bit addresses.", None),
        ("Subnetting", "What is subnetting?", ["Network Layer"], "Dividing a single IP network into multiple smaller logical sub-networks.", None),
        ("BGP", "What is BGP?", ["Routing"], "Border Gateway Protocol, the routing protocol that makes the internet work by routing traffic across autonomous systems.", None)
    ],
    "System Design": [
        ("URL Shortener", "Design a URL shortener like bit.ly.", ["Architecture"], "Use a highly available datastore, generate unique hashes, handle redirects.", None),
        ("Load Balancing", "What is a load balancer and how does it work?", ["Scalability"], "Distributes incoming network traffic across multiple servers to ensure reliability and capacity.", None),
        ("Caching Strategies", "Explain different caching strategies.", ["Performance"], "Write-through, write-around, write-back, cache-aside.", None),
        ("Microservices", "Pros and cons of Microservices vs Monolith.", ["Architecture"], "Pros: Independent deployment, scaling, tech stacks. Cons: Complexity, network overhead, data consistency.", None),
        ("Database Sharding", "What is database sharding?", ["Scalability"], "Splitting a database horizontally across multiple servers to distribute load and data.", None),
        ("Message Queues", "When would you use a message queue like Kafka or RabbitMQ?", ["Architecture", "Asynchronous"], "To decouple services, handle asynchronous processing, and buffer spikes in traffic.", None),
        ("Rate Limiting", "How would you design a rate limiter?", ["API Design"], "Use algorithms like Token Bucket, Leaky Bucket, or Sliding Window Log via Redis.", None),
        ("Consistent Hashing", "Explain consistent hashing.", ["Distributed Systems"], "A hashing technique that minimizes the number of keys that need to be remapped when a hash table is resized.", None)
    ],
    "Behavioral": [
        ("Conflict", "Tell me about a time you had a conflict with a coworker.", ["Teamwork"], "STAR method: Situation, Task, Action, Result. Focus on resolution and empathy.", None),
        ("Failure", "Tell me about a time you failed.", ["Self-Awareness"], "Focus on what you learned and how you adapted, not just the failure itself.", None),
        ("Leadership", "Tell me about a time you showed leadership.", ["Leadership"], "Taking initiative, guiding a team, or owning a project.", None),
        ("Tight Deadline", "How do you handle tight deadlines?", ["Time Management"], "Prioritization, communication with stakeholders, cutting non-essential scope.", None),
        ("Constructive Feedback", "Tell me about a time you received difficult feedback.", ["Growth Mindset"], "Listening, understanding, and actionable changes made.", None),
        ("Disagreement with Manager", "Tell me about a time you disagreed with your manager.", ["Communication"], "Professional discussion, data-driven arguments, and disagree-and-commit if necessary.", None),
        ("Proudest Achievement", "What is your proudest professional achievement?", ["Motivation"], "Highlight impact, complexity, and your specific role.", None),
        ("Learning", "Tell me about a time you had to learn a new technology quickly.", ["Adaptability"], "Reading docs, building prototypes, and applying it successfully to the project.", None)
    ]
}

for topic, q_list in templates.items():
    for i, q in enumerate(q_list):
        diff = 1 + (i % 10) # 1-10 scale
        
        q_obj = {
            "id": str(uuid.uuid4()),
            "title": q[0],
            "question": q[1],
            "topic": topic,
            "difficulty": diff,
            "concepts": q[2],
            "tags": [topic.lower().replace(" ", "_"), "interview"],
            "expected_answer": q[3],
            "sample_code": q[4],
            "language": "python" if q[4] else None,
            "hints": ["Consider the basics of " + q[0]]
        }
        questions.append(q_obj)

os.makedirs("data/questions", exist_ok=True)
with open("data/questions/seed_questions.json", "w") as f:
    json.dump(questions, f, indent=2)

print(f"Generated {len(questions)} questions in data/questions/seed_questions.json")
