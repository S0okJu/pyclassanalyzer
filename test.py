from typing import Optional, List, Dict, Set
from enum import Enum
from pydantic import BaseModel

class ModuleType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    
    def __str__(self):
        return self.value
    
    def is_internal(self):
        return self == ModuleType.INTERNAL

class RelationType(Enum):
    HERITANCE = "heritance"
    COMPOSITION = "composition"
    
    def __str__(self):
        return self.value

class ModuleDef(BaseModel):
    name: str
    type_: Optional[ModuleType] = None

class FunctionDef(BaseModel):
    name: str
    fields: Optional[List[str]] = []

class ClassNode(BaseModel):
    module: Optional[ModuleDef] = None
    external_module: List[ModuleDef] = []
    annotations: Optional[List[str]] = []
    name: str
    attributes: Optional[List[str]] = []
    functions: Optional[List[FunctionDef]] = []
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, ClassNode):
            return self.name == other.name
        return False

class Relation(BaseModel):
    type_: RelationType
    source: str
    target: str
    
    def __hash__(self):
        return hash((self.type_, self.source, self.target))
    
    def __eq__(self, other):
        if isinstance(other, Relation):
            return (self.type_ == other.type_ and 
                   self.source == other.source and 
                   self.target == other.target)
        return False

class ClassGraph(BaseModel):
    nodes: Dict[str, ClassNode] = {}
    relations: List[Relation] = []
    
    def add_node(self, node: ClassNode) -> None:
        """그래프에 노드를 추가합니다."""
        self.nodes[node.name] = node
    
    def remove_node(self, node_name: str) -> bool:
        """그래프에서 노드를 제거합니다. 관련된 모든 관계도 함께 제거됩니다."""
        if node_name not in self.nodes:
            return False
        
        # 해당 노드와 관련된 모든 관계 제거
        self.relations = [rel for rel in self.relations 
                         if rel.source != node_name and rel.target != node_name]
        
        # 노드 제거
        del self.nodes[node_name]
        return True
    
    def add_relation(self, relation: Relation) -> bool:
        """그래프에 관계를 추가합니다."""
        # 소스와 타겟 노드가 존재하는지 확인
        if relation.source not in self.nodes or relation.target not in self.nodes:
            return False
        
        # 중복 관계 확인
        if relation not in self.relations:
            self.relations.append(relation)
            return True
        return False
    
    def remove_relation(self, relation: Relation) -> bool:
        """그래프에서 관계를 제거합니다."""
        if relation in self.relations:
            self.relations.remove(relation)
            return True
        return False
    
    def get_node(self, node_name: str) -> Optional[ClassNode]:
        """노드 이름으로 노드를 가져옵니다."""
        return self.nodes.get(node_name)
    
    def get_outgoing_relations(self, node_name: str) -> List[Relation]:
        """특정 노드에서 나가는 관계들을 반환합니다."""
        return [rel for rel in self.relations if rel.source == node_name]
    
    def get_incoming_relations(self, node_name: str) -> List[Relation]:
        """특정 노드로 들어오는 관계들을 반환합니다."""
        return [rel for rel in self.relations if rel.target == node_name]
    
    def get_relations_by_type(self, relation_type: RelationType) -> List[Relation]:
        """특정 타입의 관계들을 반환합니다."""
        return [rel for rel in self.relations if rel.type_ == relation_type]
    
    def get_neighbors(self, node_name: str) -> Set[str]:
        """특정 노드의 이웃 노드들을 반환합니다 (방향성 고려)."""
        neighbors = set()
        for rel in self.relations:
            if rel.source == node_name:
                neighbors.add(rel.target)
            elif rel.target == node_name:
                neighbors.add(rel.source)
        return neighbors
    
    def get_descendants(self, node_name: str) -> Set[str]:
        """특정 노드의 모든 후손 노드들을 반환합니다 (DFS 사용)."""
        descendants = set()
        visited = set()
        
        def dfs(current: str):
            if current in visited:
                return
            visited.add(current)
            
            for rel in self.get_outgoing_relations(current):
                descendants.add(rel.target)
                dfs(rel.target)
        
        dfs(node_name)
        return descendants
    
    def get_ancestors(self, node_name: str) -> Set[str]:
        """특정 노드의 모든 조상 노드들을 반환합니다."""
        ancestors = set()
        visited = set()
        
        def dfs(current: str):
            if current in visited:
                return
            visited.add(current)
            
            for rel in self.get_incoming_relations(current):
                ancestors.add(rel.source)
                dfs(rel.source)
        
        dfs(node_name)
        return ancestors
    
    def has_cycle(self) -> bool:
        """그래프에 순환이 있는지 확인합니다."""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for rel in self.get_outgoing_relations(node):
                if rel.target not in visited:
                    if dfs(rel.target):
                        return True
                elif rel.target in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node_name in self.nodes:
            if node_name not in visited:
                if dfs(node_name):
                    return True
        return False
    
    def topological_sort(self) -> Optional[List[str]]:
        """위상 정렬을 수행합니다. 순환이 있으면 None을 반환합니다."""
        if self.has_cycle():
            return None
        
        visited = set()
        stack = []
        
        def dfs(node: str):
            visited.add(node)
            for rel in self.get_outgoing_relations(node):
                if rel.target not in visited:
                    dfs(rel.target)
            stack.append(node)
        
        for node_name in self.nodes:
            if node_name not in visited:
                dfs(node_name)
        
        return stack[::-1]
    
    def get_graph_info(self) -> Dict:
        """그래프의 기본 정보를 반환합니다."""
        inheritance_count = len(self.get_relations_by_type(RelationType.HERITANCE))
        composition_count = len(self.get_relations_by_type(RelationType.COMPOSITION))
        
        return {
            "node_count": len(self.nodes),
            "relation_count": len(self.relations),
            "inheritance_relations": inheritance_count,
            "composition_relations": composition_count,
            "has_cycle": self.has_cycle()
        }
    
    def visualize_graph(self) -> str:
        """그래프를 간단한 텍스트 형태로 시각화합니다."""
        lines = []
        lines.append("=== Class Graph ===")
        lines.append(f"Nodes: {len(self.nodes)}")
        lines.append(f"Relations: {len(self.relations)}")
        lines.append("")
        
        lines.append("Nodes:")
        for node_name, node in self.nodes.items():
            module_info = f"({node.module.name})" if node.module else ""
            lines.append(f"  - {node_name} {module_info}")
        
        lines.append("")
        lines.append("Relations:")
        for rel in self.relations:
            arrow = "──>" if rel.type_ == RelationType.HERITANCE else "◇──>"
            lines.append(f"  {rel.source} {arrow} {rel.target} ({rel.type_})")
        
        return "\n".join(lines)


# 복잡한 테스트 케이스
def create_complex_test_cases():
    """복잡한 테스트 케이스들을 생성하고 실행합니다."""
    
    print("=" * 60)
    print("COMPLEX TEST CASES")
    print("=" * 60)
    
    # 테스트 케이스 1: 대규모 상속 계층구조
    print("\n1. 대규모 상속 계층구조 테스트")
    print("-" * 40)
    
    graph1 = create_inheritance_hierarchy()
    print(graph1.visualize_graph())
    print(f"Graph Info: {graph1.get_graph_info()}")
    print(f"Object descendants: {graph1.get_descendants('Object')}")
    print(f"DatabaseModel ancestors: {graph1.get_ancestors('DatabaseModel')}")
    
    # 테스트 케이스 2: 복합 관계 (상속 + 구성)
    print("\n2. 복합 관계 (상속 + 구성) 테스트")
    print("-" * 40)
    
    graph2 = create_mixed_relationships()
    print(graph2.visualize_graph())
    print(f"Graph Info: {graph2.get_graph_info()}")
    print(f"Order composition targets: {[rel.target for rel in graph2.get_outgoing_relations('Order') if rel.type_ == RelationType.COMPOSITION]}")
    
    # 테스트 케이스 3: 순환 관계 테스트
    print("\n3. 순환 관계 테스트")
    print("-" * 40)
    
    graph3 = create_cyclic_graph()
    print(graph3.visualize_graph())
    print(f"Has cycle: {graph3.has_cycle()}")
    print(f"Topological sort: {graph3.topological_sort()}")
    
    # 테스트 케이스 4: 다중 모듈 시스템
    print("\n4. 다중 모듈 시스템 테스트")
    print("-" * 40)
    
    graph4 = create_multi_module_system()
    print(graph4.visualize_graph())
    print(f"Graph Info: {graph4.get_graph_info()}")
    
    # 테스트 케이스 5: 에러 케이스 및 엣지 케이스
    print("\n5. 에러 케이스 및 엣지 케이스 테스트")
    print("-" * 40)
    
    test_error_cases()
    
    # 테스트 케이스 6: 성능 테스트
    print("\n6. 성능 테스트 (100개 노드)")
    print("-" * 40)
    
    performance_test()

def create_inheritance_hierarchy():
    """복잡한 상속 계층구조를 생성합니다."""
    graph = ClassGraph()
    
    # 다양한 모듈 정의
    core_module = ModuleDef(name="core", type_=ModuleType.INTERNAL)
    models_module = ModuleDef(name="models", type_=ModuleType.INTERNAL)
    auth_module = ModuleDef(name="auth", type_=ModuleType.INTERNAL)
    external_orm = ModuleDef(name="sqlalchemy", type_=ModuleType.EXTERNAL)
    
    # 기본 계층
    nodes_data = [
        ("Object", core_module, ["__hash__", "__eq__"], ["__init__", "__str__"]),
        ("Serializable", core_module, ["_data"], ["serialize", "deserialize"]),
        ("Timestamped", core_module, ["created_at", "updated_at"], ["touch"]),
        ("BaseModel", models_module, ["id"], ["save", "delete", "find"]),
        ("User", auth_module, ["username", "email", "password_hash"], ["authenticate", "set_password"]),
        ("AdminUser", auth_module, ["admin_level"], ["grant_permission", "revoke_permission"]),
        ("SuperUser", auth_module, ["super_powers"], ["system_command"]),
        ("DatabaseModel", models_module, ["table_name"], ["create_table", "drop_table"]),
        ("CachedModel", models_module, ["cache_key"], ["invalidate_cache"]),
        ("AuditableModel", models_module, ["audit_log"], ["log_change"]),
    ]
    
    # 노드 생성 및 추가
    for name, module, attributes, function_names in nodes_data:
        functions = [FunctionDef(name=fname) for fname in function_names]
        node = ClassNode(
            name=name,
            module=module,
            attributes=attributes,
            functions=functions,
            annotations=["@dataclass"] if "Model" in name else []
        )
        graph.add_node(node)
    
    # 상속 관계 정의
    inheritance_relations = [
        ("Serializable", "Object"),
        ("Timestamped", "Object"),
        ("BaseModel", "Serializable"),
        ("BaseModel", "Timestamped"),  # 다중 상속
        ("DatabaseModel", "BaseModel"),
        ("CachedModel", "BaseModel"),
        ("AuditableModel", "DatabaseModel"),
        ("User", "AuditableModel"),
        ("AdminUser", "User"),
        ("SuperUser", "AdminUser"),
    ]
    
    for source, target in inheritance_relations:
        graph.add_relation(Relation(
            type_=RelationType.HERITANCE,
            source=source,
            target=target
        ))
    
    return graph

def create_mixed_relationships():
    """상속과 구성 관계가 혼합된 복합 시스템을 생성합니다."""
    graph = ClassGraph()
    
    ecommerce_module = ModuleDef(name="ecommerce", type_=ModuleType.INTERNAL)
    payment_module = ModuleDef(name="payment", type_=ModuleType.INTERNAL)
    external_stripe = ModuleDef(name="stripe", type_=ModuleType.EXTERNAL)
    
    # 전자상거래 시스템 노드들
    nodes_data = [
        ("Entity", ["id", "created_at"], ["save", "delete"]),
        ("Product", ["name", "price", "stock"], ["update_stock", "apply_discount"]),
        ("DigitalProduct", ["download_url", "license_key"], ["generate_license"]),
        ("PhysicalProduct", ["weight", "dimensions"], ["calculate_shipping"]),
        ("Customer", ["name", "email", "address"], ["place_order", "get_history"]),
        ("PremiumCustomer", ["loyalty_points", "discount_rate"], ["redeem_points"]),
        ("Order", ["total_amount", "status"], ["calculate_total", "process"]),
        ("OrderItem", ["quantity", "unit_price"], ["calculate_subtotal"]),
        ("Payment", ["amount", "method"], ["process_payment", "refund"]),
        ("CreditCardPayment", ["card_number", "cvv"], ["validate_card"]),
        ("PayPalPayment", ["paypal_email"], ["authenticate_paypal"]),
        ("ShoppingCart", ["items", "discount"], ["add_item", "remove_item", "checkout"]),
        ("Inventory", ["products", "stock_levels"], ["update_stock", "check_availability"]),
        ("Notification", ["message", "recipient"], ["send"]),
        ("EmailNotification", ["subject", "body"], ["send_email"]),
        ("SMSNotification", ["phone_number"], ["send_sms"]),
    ]
    
    # 노드 생성
    for name, attributes, function_names in nodes_data:
        functions = [FunctionDef(name=fname) for fname in function_names]
        node = ClassNode(
            name=name,
            module=ecommerce_module,
            attributes=attributes,
            functions=functions
        )
        graph.add_node(node)
    
    # 상속 관계
    inheritance_relations = [
        ("Product", "Entity"),
        ("Customer", "Entity"),
        ("Order", "Entity"),
        ("Payment", "Entity"),
        ("DigitalProduct", "Product"),
        ("PhysicalProduct", "Product"),
        ("PremiumCustomer", "Customer"),
        ("CreditCardPayment", "Payment"),
        ("PayPalPayment", "Payment"),
        ("EmailNotification", "Notification"),
        ("SMSNotification", "Notification"),
    ]
    
    for source, target in inheritance_relations:
        graph.add_relation(Relation(
            type_=RelationType.HERITANCE,
            source=source,
            target=target
        ))
    
    # 구성 관계 (has-a relationships)
    composition_relations = [
        ("Order", "Customer"),      # Order has a Customer
        ("Order", "Payment"),       # Order has a Payment
        ("OrderItem", "Product"),   # OrderItem has a Product
        ("Order", "OrderItem"),     # Order has OrderItems
        ("ShoppingCart", "Product"), # ShoppingCart has Products
        ("ShoppingCart", "Customer"), # ShoppingCart belongs to Customer
        ("Inventory", "Product"),   # Inventory manages Products
        ("Order", "Notification"),  # Order triggers Notifications
    ]
    
    for source, target in composition_relations:
        graph.add_relation(Relation(
            type_=RelationType.COMPOSITION,
            source=source,
            target=target
        ))
    
    return graph

def create_cyclic_graph():
    """순환 관계가 있는 그래프를 생성합니다."""
    graph = ClassGraph()
    
    module = ModuleDef(name="cyclic_test", type_=ModuleType.INTERNAL)
    
    # 순환 관계를 만들 노드들
    nodes = ["A", "B", "C", "D", "E"]
    for name in nodes:
        node = ClassNode(
            name=name,
            module=module,
            attributes=[f"{name.lower()}_attr"],
            functions=[FunctionDef(name=f"{name.lower()}_method")]
        )
        graph.add_node(node)
    
    # 순환 관계 생성: A -> B -> C -> A, D -> E -> D
    cyclic_relations = [
        ("A", "B"),
        ("B", "C"),
        ("C", "A"),  # 순환!
        ("D", "E"),
        ("E", "D"),  # 또 다른 순환!
    ]
    
    for source, target in cyclic_relations:
        graph.add_relation(Relation(
            type_=RelationType.HERITANCE,
            source=source,
            target=target
        ))
    
    return graph

def create_multi_module_system():
    """다중 모듈 시스템을 생성합니다."""
    graph = ClassGraph()
    
    # 다양한 모듈들
    modules = {
        "core": ModuleDef(name="core", type_=ModuleType.INTERNAL),
        "web": ModuleDef(name="web", type_=ModuleType.INTERNAL),
        "database": ModuleDef(name="database", type_=ModuleType.INTERNAL),
        "django": ModuleDef(name="django.db.models", type_=ModuleType.EXTERNAL),
        "flask": ModuleDef(name="flask", type_=ModuleType.EXTERNAL),
        "sqlalchemy": ModuleDef(name="sqlalchemy", type_=ModuleType.EXTERNAL),
    }
    
    # 모듈별 클래스들
    classes_by_module = {
        "core": [
            ("Logger", ["level", "handlers"], ["log", "debug", "error"]),
            ("Config", ["settings"], ["get", "set", "load"]),
            ("Cache", ["store", "ttl"], ["get", "set", "invalidate"]),
        ],
        "web": [
            ("Request", ["headers", "body", "method"], ["get_header", "get_param"]),
            ("Response", ["status", "headers", "body"], ["set_header", "write"]),
            ("Controller", ["request", "response"], ["handle", "render"]),
            ("Middleware", ["next"], ["process"]),
        ],
        "database": [
            ("Connection", ["host", "port", "database"], ["connect", "disconnect", "execute"]),
            ("Query", ["sql", "params"], ["execute", "fetch_all", "fetch_one"]),
            ("Transaction", ["connection"], ["begin", "commit", "rollback"]),
        ]
    }
    
    # 노드 생성
    for module_name, classes in classes_by_module.items():
        for class_name, attributes, function_names in classes:
            functions = [FunctionDef(name=fname) for fname in function_names]
            node = ClassNode(
                name=class_name,
                module=modules[module_name],
                external_module=[modules["django"], modules["flask"]] if module_name == "web" else [],
                attributes=attributes,
                functions=functions,
                annotations=["@singleton"] if class_name in ["Logger", "Config", "Cache"] else []
            )
            graph.add_node(node)
    
    # 모듈 간 의존성 관계
    cross_module_relations = [
        # web -> core dependencies
        ("Controller", "Logger", RelationType.COMPOSITION),
        ("Controller", "Config", RelationType.COMPOSITION),
        ("Middleware", "Cache", RelationType.COMPOSITION),
        
        # database -> core dependencies  
        ("Connection", "Logger", RelationType.COMPOSITION),
        ("Connection", "Config", RelationType.COMPOSITION),
        
        # web -> database dependencies
        ("Controller", "Connection", RelationType.COMPOSITION),
        ("Controller", "Query", RelationType.COMPOSITION),
    ]
    
    for source, target, rel_type in cross_module_relations:
        graph.add_relation(Relation(
            type_=rel_type,
            source=source,
            target=target
        ))
    
    return graph

def test_error_cases():
    """에러 케이스와 엣지 케이스를 테스트합니다."""
    graph = ClassGraph()
    
    # 기본 노드 추가
    node1 = ClassNode(name="TestNode1")
    node2 = ClassNode(name="TestNode2")
    graph.add_node(node1)
    graph.add_node(node2)
    
    print("에러 케이스 테스트:")
    
    # 1. 존재하지 않는 노드로의 관계 추가 시도
    result = graph.add_relation(Relation(
        type_=RelationType.HERITANCE,
        source="TestNode1",
        target="NonExistentNode"
    ))
    print(f"비존재 노드 관계 추가: {result} (False 예상)")
    
    # 2. 중복 관계 추가 시도
    graph.add_relation(Relation(
        type_=RelationType.HERITANCE,
        source="TestNode1",
        target="TestNode2"
    ))
    result = graph.add_relation(Relation(
        type_=RelationType.HERITANCE,
        source="TestNode1",
        target="TestNode2"
    ))
    print(f"중복 관계 추가: {result} (False 예상)")
    
    # 3. 존재하지 않는 노드 제거 시도
    result = graph.remove_node("NonExistentNode")
    print(f"비존재 노드 제거: {result} (False 예상)")
    
    # 4. 빈 그래프에서 연산들
    empty_graph = ClassGraph()
    print(f"빈 그래프 순환 검사: {empty_graph.has_cycle()} (False 예상)")
    print(f"빈 그래프 위상정렬: {empty_graph.topological_sort()} ([] 예상)")
    
    # 5. 자기 자신으로의 관계 (self-loop)
    graph.add_relation(Relation(
        type_=RelationType.COMPOSITION,
        source="TestNode1",
        target="TestNode1"
    ))
    print(f"Self-loop 후 순환 검사: {graph.has_cycle()}")

def performance_test():
    """성능 테스트를 위한 대규모 그래프 생성."""
    import time
    
    graph = ClassGraph()
    module = ModuleDef(name="perf_test", type_=ModuleType.INTERNAL)
    
    # 100개 노드 생성
    start_time = time.time()
    for i in range(100):
        node = ClassNode(
            name=f"Node{i}",
            module=module,
            attributes=[f"attr_{i}"],
            functions=[FunctionDef(name=f"method_{i}")]
        )
        graph.add_node(node)
    
    # 200개 관계 생성 (각 노드마다 평균 2개 관계)
    for i in range(100):
        # 각 노드에서 다음 노드로 상속 관계
        if i < 99:
            graph.add_relation(Relation(
                type_=RelationType.HERITANCE,
                source=f"Node{i}",
                target=f"Node{i+1}"
            ))
        
        # 일부 노드들에 구성 관계 추가
        if i % 3 == 0 and i < 97:
            graph.add_relation(Relation(
                type_=RelationType.COMPOSITION,
                source=f"Node{i}",
                target=f"Node{i+3}"
            ))
    
    creation_time = time.time() - start_time
    
    # 성능 측정
    start_time = time.time()
    has_cycle = graph.has_cycle()
    cycle_check_time = time.time() - start_time
    
    start_time = time.time()
    topo_sort = graph.topological_sort()
    topo_sort_time = time.time() - start_time
    
    start_time = time.time()
    descendants = graph.get_descendants("Node0")
    descendants_time = time.time() - start_time
    
    print(f"그래프 생성 시간: {creation_time:.4f}초")
    print(f"순환 검사 시간: {cycle_check_time:.4f}초")
    print(f"위상 정렬 시간: {topo_sort_time:.4f}초")
    print(f"후손 검색 시간: {descendants_time:.4f}초")
    print(f"Node0의 후손 개수: {len(descendants)}")
    print(f"위상 정렬 성공: {topo_sort is not None}")
    print(f"그래프 정보: {graph.get_graph_info()}")

# 기본 사용 예제
def basic_example():
    """기본 사용 예제"""
    print("=" * 60)
    print("BASIC EXAMPLE")
    print("=" * 60)
    
    # 그래프 생성
    graph = ClassGraph()
    
    # 모듈 정의
    internal_module = ModuleDef(name="models", type_=ModuleType.INTERNAL)
    external_module = ModuleDef(name="django.db", type_=ModuleType.EXTERNAL)
    
    # 노드 생성
    base_node = ClassNode(
        name="BaseModel",
        module=internal_module,
        attributes=["id", "created_at"],
        functions=[FunctionDef(name="save"), FunctionDef(name="delete")]
    )
    
    user_node = ClassNode(
        name="User",
        module=internal_module,
        attributes=["username", "email"],
        functions=[FunctionDef(name="authenticate")]
    )
    
    admin_node = ClassNode(
        name="Admin",
        module=internal_module,
        attributes=["permissions"],
        functions=[FunctionDef(name="grant_permission")]
    )
    
    # 노드 추가
    graph.add_node(base_node)
    graph.add_node(user_node)
    graph.add_node(admin_node)
    
    # 관계 추가
    graph.add_relation(Relation(
        type_=RelationType.HERITANCE,
        source="User",
        target="BaseModel"
    ))
    
    graph.add_relation(Relation(
        type_=RelationType.HERITANCE,
        source="Admin",
        target="User"
    ))
    
    # 그래프 정보 출력
    print(graph.visualize_graph())
    print(f"\nGraph Info: {graph.get_graph_info()}")
    print(f"BaseModel descendants: {graph.get_descendants('BaseModel')}")
    print(f"Admin ancestors: {graph.get_ancestors('Admin')}")
    print(f"Topological sort: {graph.topological_sort()}")

# 메인 실행
if __name__ == "__main__":
    basic_example()
    create_complex_test_cases()