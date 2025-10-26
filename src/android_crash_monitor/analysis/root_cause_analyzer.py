#!/usr/bin/env python3
"""
Root Cause Analysis Engine

Performs automated root cause analysis on crashes using:
- Dependency tracking and cascading failure detection
- Fault tree analysis
- Timeline reconstruction
- Statistical causal inference
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter
from enum import Enum
import re


class CauseType(Enum):
    """Types of root causes"""
    PRIMARY = "primary"           # Direct root cause
    CONTRIBUTING = "contributing" # Contributing factor
    TRIGGER = "trigger"           # Immediate trigger
    SYMPTOM = "symptom"           # Symptom, not cause


class ComponentType(Enum):
    """System component types"""
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    UI = "ui"
    SYSTEM = "system"
    APP_LOGIC = "app_logic"
    THIRD_PARTY = "third_party"
    HARDWARE = "hardware"


class FailureMode(Enum):
    """Common failure modes"""
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEADLOCK = "deadlock"
    RACE_CONDITION = "race_condition"
    MEMORY_LEAK = "memory_leak"
    CONFIGURATION_ERROR = "configuration_error"
    DATA_CORRUPTION = "data_corruption"
    EXTERNAL_DEPENDENCY = "external_dependency"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    INITIALIZATION_FAILURE = "initialization_failure"


@dataclass
class CrashDependency:
    """Represents a dependency relationship between crashes"""
    source_crash_id: str
    target_crash_id: str
    dependency_type: str  # e.g., "triggers", "follows", "related_to"
    confidence: float     # 0-1
    time_delta: float     # Time difference in seconds
    evidence: List[str] = field(default_factory=list)


@dataclass
class Component:
    """Represents a system component"""
    name: str
    component_type: ComponentType
    health_score: float = 1.0  # 0-1, 1 = healthy
    failure_count: int = 0
    related_crashes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Component names


@dataclass
class FaultTreeNode:
    """Node in a fault tree"""
    event: str
    event_type: str  # "root", "intermediate", "basic"
    probability: float = 0.0
    children: List['FaultTreeNode'] = field(default_factory=list)
    gate_type: str = "OR"  # "AND" or "OR"
    evidence: List[str] = field(default_factory=list)


@dataclass
class CausalChain:
    """Represents a causal chain of events"""
    chain_id: str
    events: List[Dict] = field(default_factory=list)  # Ordered list of events
    root_cause: Optional[str] = None
    confidence: float = 0.0
    failure_mode: Optional[FailureMode] = None
    affected_components: List[str] = field(default_factory=list)


@dataclass
class RootCauseAnalysis:
    """Complete root cause analysis result"""
    analysis_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Root causes identified
    primary_root_causes: List[Dict] = field(default_factory=list)
    contributing_factors: List[Dict] = field(default_factory=list)
    
    # Analysis artifacts
    fault_tree: Optional[FaultTreeNode] = None
    causal_chains: List[CausalChain] = field(default_factory=list)
    component_health: Dict[str, Component] = field(default_factory=dict)
    
    # Dependencies
    crash_dependencies: List[CrashDependency] = field(default_factory=list)
    component_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    # Confidence and evidence
    overall_confidence: float = 0.0
    evidence_summary: List[str] = field(default_factory=list)
    
    # Recommendations
    remediation_steps: List[str] = field(default_factory=list)
    prevention_measures: List[str] = field(default_factory=list)


class DependencyAnalyzer:
    """Analyzes crash dependencies and relationships"""
    
    def __init__(self):
        self.component_keywords = {
            ComponentType.MEMORY: ['memory', 'heap', 'oom', 'allocation', 'gc'],
            ComponentType.STORAGE: ['storage', 'disk', 'file', 'io', 'sqlite'],
            ComponentType.NETWORK: ['network', 'connection', 'socket', 'http', 'timeout'],
            ComponentType.DATABASE: ['database', 'sql', 'query', 'transaction', 'db'],
            ComponentType.UI: ['ui', 'view', 'activity', 'fragment', 'render', 'layout'],
            ComponentType.SYSTEM: ['system', 'native', 'kernel', 'permission', 'service'],
            ComponentType.APP_LOGIC: ['nullpointer', 'exception', 'assertion', 'logic'],
            ComponentType.THIRD_PARTY: ['library', 'sdk', 'third-party', 'vendor'],
        }
    
    def analyze_dependencies(self, crashes: List[Dict]) -> Tuple[List[CrashDependency], Dict[str, Component]]:
        """Analyze crash dependencies and component health"""
        dependencies = []
        components = {}
        
        # Identify components affected by each crash
        crash_components = {}
        for crash in crashes:
            crash_id = crash.get('title', str(crashes.index(crash)))
            affected = self._identify_affected_components(crash)
            crash_components[crash_id] = affected
            
            # Update component health
            for comp_name, comp_type in affected:
                if comp_name not in components:
                    components[comp_name] = Component(comp_name, comp_type)
                components[comp_name].failure_count += 1
                components[comp_name].related_crashes.append(crash_id)
        
        # Find temporal dependencies
        # Sort by timestamp, putting None timestamps last
        sorted_crashes = sorted(crashes, key=lambda c: self._parse_timestamp(c.get('timestamp', '')) or datetime.min)
        
        for i, crash1 in enumerate(sorted_crashes):
            crash1_id = crash1.get('title', str(i))
            crash1_time = self._parse_timestamp(crash1.get('timestamp', ''))
            
            if not crash1_time:
                continue
            
            # Look for related crashes within time window
            for j in range(i + 1, min(i + 10, len(sorted_crashes))):
                crash2 = sorted_crashes[j]
                crash2_id = crash2.get('title', str(j))
                crash2_time = self._parse_timestamp(crash2.get('timestamp', ''))
                
                if not crash2_time:
                    continue
                
                time_delta = (crash2_time - crash1_time).total_seconds()
                
                # Skip if too far apart
                if time_delta > 300:  # 5 minutes
                    break
                
                # Check for dependency
                dep_type, confidence, evidence = self._infer_dependency(
                    crash1, crash2, crash_components.get(crash1_id, []),
                    crash_components.get(crash2_id, []), time_delta
                )
                
                if confidence > 0.5:
                    dependencies.append(CrashDependency(
                        source_crash_id=crash1_id,
                        target_crash_id=crash2_id,
                        dependency_type=dep_type,
                        confidence=confidence,
                        time_delta=time_delta,
                        evidence=evidence
                    ))
        
        # Calculate component health scores
        for comp in components.values():
            # Health decreases with failure count
            comp.health_score = max(0.0, 1.0 - (comp.failure_count * 0.1))
        
        return dependencies, components
    
    def _identify_affected_components(self, crash: Dict) -> List[Tuple[str, ComponentType]]:
        """Identify which components are affected by a crash"""
        affected = []
        description = crash.get('description', '').lower()
        
        for comp_type, keywords in self.component_keywords.items():
            if any(kw in description for kw in keywords):
                # Extract more specific component name if possible
                comp_name = self._extract_component_name(description, comp_type)
                affected.append((comp_name, comp_type))
        
        return affected if affected else [("Unknown", ComponentType.APP_LOGIC)]
    
    def _extract_component_name(self, description: str, comp_type: ComponentType) -> str:
        """Extract specific component name from description"""
        # Try to extract class names, package names, etc.
        
        # Look for Java/Android class names
        class_pattern = r'([a-z][a-z0-9_]*\.)+[A-Z][a-zA-Z0-9_]*'
        matches = re.findall(class_pattern, description)
        if matches:
            return matches[0]
        
        # Use component type as fallback
        return comp_type.value.replace('_', ' ').title()
    
    def _infer_dependency(self, crash1: Dict, crash2: Dict, 
                         comps1: List[Tuple], comps2: List[Tuple],
                         time_delta: float) -> Tuple[str, float, List[str]]:
        """Infer dependency relationship between two crashes"""
        evidence = []
        confidence = 0.0
        dep_type = "related_to"
        
        # Check for component overlap
        comp_types1 = {c[1] for c in comps1}
        comp_types2 = {c[1] for c in comps2}
        overlap = comp_types1 & comp_types2
        
        if overlap:
            evidence.append(f"Both affect {', '.join(c.value for c in overlap)}")
            confidence += 0.3
        
        # Check for cascading patterns
        desc1 = crash1.get('description', '').lower()
        desc2 = crash2.get('description', '').lower()
        
        # Memory exhaustion often triggers other crashes
        if any(kw in desc1 for kw in ['memory', 'oom', 'heap']) and time_delta < 60:
            evidence.append("Memory exhaustion in first crash can trigger subsequent failures")
            confidence += 0.4
            dep_type = "triggers"
        
        # Database locks can cause cascading failures
        if 'database' in desc1 and 'timeout' in desc2 and time_delta < 30:
            evidence.append("Database issue followed by timeout suggests cascade")
            confidence += 0.4
            dep_type = "triggers"
        
        # Same app crashes repeatedly
        app1 = crash1.get('app_name', '')
        app2 = crash2.get('app_name', '')
        if app1 == app2 and app1:
            evidence.append(f"Both crashes in same app: {app1}")
            confidence += 0.2
        
        # Very close in time
        if time_delta < 5:
            evidence.append(f"Crashes very close in time ({time_delta:.1f}s)")
            confidence += 0.2
            dep_type = "follows"
        
        return dep_type, min(confidence, 1.0), evidence
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse crash timestamp"""
        if not timestamp_str:
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%m-%d %H:%M:%S.%f',
            '%m-%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(timestamp_str.strip(), fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=datetime.now().year)
                return parsed
            except ValueError:
                continue
        
        return None


class FaultTreeAnalyzer:
    """Builds fault trees to identify root causes"""
    
    def build_fault_tree(self, crashes: List[Dict], dependencies: List[CrashDependency],
                        components: Dict[str, Component]) -> FaultTreeNode:
        """Build fault tree from crash data"""
        
        # Top event: System failure (multiple crashes)
        root = FaultTreeNode(
            event="Multiple Crash Failures",
            event_type="root",
            gate_type="OR"
        )
        
        # Group crashes by failure mode
        failure_groups = self._group_by_failure_mode(crashes, components)
        
        for failure_mode, mode_crashes in failure_groups.items():
            if not mode_crashes:
                continue
            
            # Create intermediate node for this failure mode
            mode_node = FaultTreeNode(
                event=f"{failure_mode.value.replace('_', ' ').title()} Failure",
                event_type="intermediate",
                gate_type="AND" if len(mode_crashes) > 3 else "OR",
                probability=len(mode_crashes) / len(crashes)
            )
            
            # Add basic events (individual crashes)
            for crash in mode_crashes[:5]:  # Limit to top 5
                crash_node = FaultTreeNode(
                    event=crash.get('title', 'Unknown Crash'),
                    event_type="basic",
                    evidence=[crash.get('description', '')[:100]]
                )
                mode_node.children.append(crash_node)
            
            root.children.append(mode_node)
        
        # Calculate probabilities up the tree
        self._calculate_probabilities(root)
        
        return root
    
    def _group_by_failure_mode(self, crashes: List[Dict], 
                               components: Dict[str, Component]) -> Dict[FailureMode, List[Dict]]:
        """Group crashes by likely failure mode"""
        groups = defaultdict(list)
        
        for crash in crashes:
            mode = self._identify_failure_mode(crash, components)
            groups[mode].append(crash)
        
        return dict(groups)
    
    def _identify_failure_mode(self, crash: Dict, components: Dict[str, Component]) -> FailureMode:
        """Identify the failure mode from crash characteristics"""
        desc = crash.get('description', '').lower()
        
        # Memory-related
        if any(kw in desc for kw in ['memory', 'oom', 'heap', 'allocation']):
            if 'leak' in desc:
                return FailureMode.MEMORY_LEAK
            return FailureMode.RESOURCE_EXHAUSTION
        
        # Deadlock/race condition
        if any(kw in desc for kw in ['deadlock', 'blocked', 'waiting']):
            return FailureMode.DEADLOCK
        if any(kw in desc for kw in ['race', 'concurrent', 'thread']):
            return FailureMode.RACE_CONDITION
        
        # Database/data issues
        if any(kw in desc for kw in ['corrupt', 'invalid', 'malformed']):
            return FailureMode.DATA_CORRUPTION
        
        # Configuration
        if any(kw in desc for kw in ['config', 'setting', 'property', 'missing']):
            return FailureMode.CONFIGURATION_ERROR
        
        # External dependencies
        if any(kw in desc for kw in ['network', 'timeout', 'connection', 'unavailable']):
            return FailureMode.EXTERNAL_DEPENDENCY
        
        # Performance
        if any(kw in desc for kw in ['slow', 'anr', 'timeout', 'hung']):
            return FailureMode.PERFORMANCE_DEGRADATION
        
        # Initialization
        if any(kw in desc for kw in ['init', 'start', 'onCreate', 'constructor']):
            return FailureMode.INITIALIZATION_FAILURE
        
        # Default
        return FailureMode.RESOURCE_EXHAUSTION
    
    def _calculate_probabilities(self, node: FaultTreeNode) -> float:
        """Calculate failure probabilities recursively"""
        if node.event_type == "basic":
            node.probability = 0.1  # Base probability for leaf events
            return node.probability
        
        if not node.children:
            node.probability = 0.0
            return 0.0
        
        # Calculate child probabilities first
        child_probs = [self._calculate_probabilities(child) for child in node.children]
        
        # Calculate node probability based on gate type
        if node.gate_type == "AND":
            # All children must fail
            node.probability = 1.0
            for p in child_probs:
                node.probability *= p
        else:  # OR gate
            # At least one child must fail
            node.probability = 1.0
            for p in child_probs:
                node.probability *= (1.0 - p)
            node.probability = 1.0 - node.probability
        
        return node.probability


class CausalInferenceEngine:
    """Performs statistical causal inference to identify root causes"""
    
    def infer_causal_chains(self, crashes: List[Dict], dependencies: List[CrashDependency],
                           components: Dict[str, Component]) -> List[CausalChain]:
        """Infer causal chains from crash data"""
        chains = []
        
        # Build dependency graph
        dep_graph = defaultdict(list)
        for dep in dependencies:
            dep_graph[dep.source_crash_id].append(dep)
        
        # Find root crashes (no incoming dependencies)
        root_crashes = set(crash.get('title', str(i)) for i, crash in enumerate(crashes))
        for dep in dependencies:
            root_crashes.discard(dep.target_crash_id)
        
        # Build chains starting from each root
        for root_id in root_crashes:
            chain = self._build_chain_from_root(root_id, dep_graph, crashes, components)
            if chain and len(chain.events) > 1:
                chains.append(chain)
        
        return chains
    
    def _build_chain_from_root(self, root_id: str, dep_graph: Dict,
                               crashes: List[Dict], components: Dict[str, Component]) -> CausalChain:
        """Build causal chain starting from a root crash"""
        chain = CausalChain(
            chain_id=f"chain_{root_id}",
            root_cause=root_id
        )
        
        # Find root crash
        root_crash = next((c for c in crashes if c.get('title', '') == root_id), None)
        if not root_crash:
            return chain
        
        # Add root event
        chain.events.append({
            'crash_id': root_id,
            'description': root_crash.get('description', ''),
            'timestamp': root_crash.get('timestamp', ''),
            'role': 'root_cause'
        })
        
        # Follow dependency chain
        visited = {root_id}
        current_id = root_id
        chain_confidence = 1.0
        
        while current_id in dep_graph:
            # Get highest confidence dependency
            deps = sorted(dep_graph[current_id], key=lambda d: d.confidence, reverse=True)
            if not deps:
                break
            
            best_dep = deps[0]
            if best_dep.target_crash_id in visited:
                break  # Avoid cycles
            
            # Find target crash
            target_crash = next((c for c in crashes 
                               if c.get('title', '') == best_dep.target_crash_id), None)
            if not target_crash:
                break
            
            # Add to chain
            chain.events.append({
                'crash_id': best_dep.target_crash_id,
                'description': target_crash.get('description', ''),
                'timestamp': target_crash.get('timestamp', ''),
                'role': 'consequence',
                'dependency_type': best_dep.dependency_type,
                'confidence': best_dep.confidence
            })
            
            chain_confidence *= best_dep.confidence
            visited.add(best_dep.target_crash_id)
            current_id = best_dep.target_crash_id
        
        chain.confidence = chain_confidence
        
        # Identify failure mode from root crash
        if root_crash:
            failure_analyzer = FaultTreeAnalyzer()
            chain.failure_mode = failure_analyzer._identify_failure_mode(root_crash, components)
        
        return chain


class RootCauseAnalyzer:
    """Main root cause analysis engine"""
    
    def __init__(self):
        self.dependency_analyzer = DependencyAnalyzer()
        self.fault_tree_analyzer = FaultTreeAnalyzer()
        self.causal_engine = CausalInferenceEngine()
    
    def analyze(self, crashes: List[Dict], analysis_id: str = None) -> RootCauseAnalysis:
        """Perform comprehensive root cause analysis"""
        if not crashes:
            return RootCauseAnalysis(analysis_id=analysis_id or "rca_empty")
        
        if not analysis_id:
            analysis_id = f"rca_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Step 1: Analyze dependencies and component health
        dependencies, components = self.dependency_analyzer.analyze_dependencies(crashes)
        
        # Step 2: Build fault tree
        fault_tree = self.fault_tree_analyzer.build_fault_tree(crashes, dependencies, components)
        
        # Step 3: Infer causal chains
        causal_chains = self.causal_engine.infer_causal_chains(crashes, dependencies, components)
        
        # Step 4: Identify root causes
        primary_causes, contributing_factors = self._identify_root_causes(
            crashes, dependencies, components, causal_chains, fault_tree
        )
        
        # Step 5: Generate recommendations
        remediation_steps, prevention_measures = self._generate_recommendations(
            primary_causes, contributing_factors, components
        )
        
        # Step 6: Compile evidence
        evidence_summary = self._compile_evidence(dependencies, causal_chains)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(primary_causes, causal_chains)
        
        return RootCauseAnalysis(
            analysis_id=analysis_id,
            primary_root_causes=primary_causes,
            contributing_factors=contributing_factors,
            fault_tree=fault_tree,
            causal_chains=causal_chains,
            component_health=components,
            crash_dependencies=dependencies,
            overall_confidence=overall_confidence,
            evidence_summary=evidence_summary,
            remediation_steps=remediation_steps,
            prevention_measures=prevention_measures
        )
    
    def _identify_root_causes(self, crashes: List[Dict], dependencies: List[CrashDependency],
                             components: Dict[str, Component], chains: List[CausalChain],
                             fault_tree: FaultTreeNode) -> Tuple[List[Dict], List[Dict]]:
        """Identify primary root causes and contributing factors"""
        primary_causes = []
        contributing_factors = []
        
        # Analyze causal chains for root causes
        root_causes_count = Counter()
        for chain in chains:
            # Lower threshold to catch more potential root causes
            if chain.root_cause and chain.confidence > 0.2:
                root_causes_count[chain.root_cause] += 1
        
        # Get most common root causes
        for root_id, count in root_causes_count.most_common(3):
            root_crash = next((c for c in crashes if c.get('title', '') == root_id), None)
            if root_crash:
                primary_causes.append({
                    'cause': root_id,
                    'description': root_crash.get('description', ''),
                    'frequency': count,
                    'confidence': 0.7 + (count / len(chains)) * 0.3,
                    'type': CauseType.PRIMARY.value
                })
        
        # Identify contributing factors from unhealthy components
        for comp_name, comp in components.items():
            if comp.health_score < 0.5 and comp.failure_count >= 2:
                contributing_factors.append({
                    'factor': comp_name,
                    'component_type': comp.component_type.value,
                    'health_score': comp.health_score,
                    'failure_count': comp.failure_count,
                    'confidence': 1.0 - comp.health_score,
                    'type': CauseType.CONTRIBUTING.value
                })
        
        # Sort by confidence
        primary_causes.sort(key=lambda x: x['confidence'], reverse=True)
        contributing_factors.sort(key=lambda x: x['confidence'], reverse=True)
        
        return primary_causes, contributing_factors
    
    def _generate_recommendations(self, primary_causes: List[Dict], 
                                 contributing_factors: List[Dict],
                                 components: Dict[str, Component]) -> Tuple[List[str], List[str]]:
        """Generate remediation and prevention recommendations"""
        remediation = []
        prevention = []
        
        # Remediation based on root causes
        if primary_causes:
            top_cause = primary_causes[0]
            desc = top_cause.get('description', '').lower()
            
            if 'memory' in desc or 'oom' in desc:
                remediation.append("Immediately investigate memory usage and potential leaks")
                remediation.append("Review recent code changes affecting memory allocation")
                prevention.append("Implement memory profiling in CI/CD pipeline")
                prevention.append("Add memory usage monitoring and alerts")
            
            if 'database' in desc:
                remediation.append("Check database connections and transaction handling")
                remediation.append("Verify database schema and migrations")
                prevention.append("Add database connection pooling")
                prevention.append("Implement database query performance monitoring")
            
            if 'network' in desc:
                remediation.append("Verify network connectivity and API endpoints")
                remediation.append("Check for timeout configuration issues")
                prevention.append("Implement retry logic with exponential backoff")
                prevention.append("Add network monitoring and circuit breakers")
        
        # Remediation based on contributing factors
        unhealthy_comps = [f for f in contributing_factors if f.get('health_score', 1.0) < 0.3]
        if unhealthy_comps:
            comp_names = ', '.join(f['factor'] for f in unhealthy_comps[:3])
            remediation.append(f"Critical: Review and stabilize components: {comp_names}")
            prevention.append("Implement comprehensive component health monitoring")
        
        # General recommendations
        if not remediation:
            remediation.append("Review error logs for common patterns")
            remediation.append("Analyze recent deployments and configuration changes")
        
        if not prevention:
            prevention.append("Increase test coverage for affected components")
            prevention.append("Implement better error handling and recovery")
        
        return remediation[:5], prevention[:5]
    
    def _compile_evidence(self, dependencies: List[CrashDependency],
                         chains: List[CausalChain]) -> List[str]:
        """Compile evidence supporting the analysis"""
        evidence = []
        
        # Dependency evidence
        high_conf_deps = [d for d in dependencies if d.confidence > 0.7]
        if high_conf_deps:
            evidence.append(f"Found {len(high_conf_deps)} high-confidence crash dependencies")
        
        # Causal chain evidence
        if chains:
            avg_chain_length = sum(len(c.events) for c in chains) / len(chains)
            evidence.append(f"Identified {len(chains)} causal chains (avg length: {avg_chain_length:.1f})")
        
        # Timing evidence
        cascade_deps = [d for d in dependencies if d.time_delta < 10]
        if cascade_deps:
            evidence.append(f"Detected {len(cascade_deps)} cascade failures within 10 seconds")
        
        return evidence
    
    def _calculate_overall_confidence(self, primary_causes: List[Dict],
                                     chains: List[CausalChain]) -> float:
        """Calculate overall analysis confidence"""
        if not primary_causes:
            return 0.0
        
        # Average confidence of top causes
        cause_conf = sum(c.get('confidence', 0) for c in primary_causes[:3]) / min(3, len(primary_causes))
        
        # Chain confidence
        chain_conf = sum(c.confidence for c in chains) / len(chains) if chains else 0.5
        
        # Weighted average
        return cause_conf * 0.7 + chain_conf * 0.3
