# 📚 Phase 3 Integration - Practical Examples

## 🎯 Real-World Scenarios

### Scenario 1: Web Development Project

```python
"""
Complete web development workflow combining all three phases:
- Phase 1: Task breakdown with subtasks
- Phase 2: Cross-list dependencies between frontend/backend
- Phase 3: Smart task prioritization and progress tracking
"""

# === PROJECT SETUP ===
mgr = TodoManager()

# Create project lists
mgr.create_list("backend", "Backend Development")
mgr.create_list("frontend", "Frontend Development") 
mgr.create_list("deployment", "Deployment & DevOps")

# Link lists to project
mgr.create_list_relation("backend", "frontend", "project", "webapp")
mgr.create_list_relation("frontend", "deployment", "project", "webapp")

# === PHASE 1: HIERARCHICAL TASK BREAKDOWN ===

# Backend tasks with subtasks
mgr.add_item("backend", "auth", "Authentication System")
mgr.add_subtask("backend", "auth", "models", "User models & database")
mgr.add_subtask("backend", "auth", "endpoints", "Auth API endpoints")
mgr.add_subtask("backend", "auth", "middleware", "Auth middleware")

mgr.add_item("backend", "api", "REST API")
mgr.add_subtask("backend", "api", "users", "User CRUD endpoints")
mgr.add_subtask("backend", "api", "posts", "Post CRUD endpoints")
mgr.add_subtask("backend", "api", "files", "File upload endpoints")

# Frontend tasks with subtasks
mgr.add_item("frontend", "components", "React Components")
mgr.add_subtask("frontend", "components", "auth_forms", "Login/Register forms")
mgr.add_subtask("frontend", "components", "user_profile", "User profile components")
mgr.add_subtask("frontend", "components", "post_list", "Post listing components")

mgr.add_item("frontend", "pages", "Application Pages")
mgr.add_subtask("frontend", "pages", "login", "Login page")
mgr.add_subtask("frontend", "pages", "dashboard", "User dashboard")
mgr.add_subtask("frontend", "pages", "profile", "Profile page")

# Deployment tasks
mgr.add_item("deployment", "ci_cd", "CI/CD Pipeline")
mgr.add_item("deployment", "prod", "Production Deployment")

# === PHASE 2: CROSS-LIST DEPENDENCIES ===

# Frontend components depend on backend APIs
mgr.add_item_dependency("frontend", "auth_forms", "backend", "endpoints")
mgr.add_item_dependency("frontend", "user_profile", "backend", "users")  
mgr.add_item_dependency("frontend", "post_list", "backend", "posts")

# Frontend pages depend on components
mgr.add_item_dependency("frontend", "login", "frontend", "auth_forms")
mgr.add_item_dependency("frontend", "dashboard", "frontend", "post_list")
mgr.add_item_dependency("frontend", "profile", "frontend", "user_profile")

# Deployment depends on both backend and frontend
mgr.add_item_dependency("deployment", "ci_cd", "backend", "auth")
mgr.add_item_dependency("deployment", "ci_cd", "frontend", "pages")
mgr.add_item_dependency("deployment", "prod", "deployment", "ci_cd")

# === PHASE 3: SMART WORKFLOW ===

print("=== PROJECT STATUS ===")

# Get next tasks for each list using Phase 3 smart algorithm
backend_next = mgr.get_next_pending_with_subtasks("backend")
frontend_next = mgr.get_next_pending_with_subtasks("frontend")
deployment_next = mgr.get_next_pending_with_subtasks("deployment")

print(f"Backend next: {backend_next.item_key if backend_next else 'None'}")
# Expected: "models" (first subtask of auth system)

print(f"Frontend next: {frontend_next.item_key if frontend_next else 'None'}")  
# Expected: None (all tasks blocked by backend dependencies)

print(f"Deployment next: {deployment_next.item_key if deployment_next else 'None'}")
# Expected: None (blocked by backend and frontend)

# === COMPREHENSIVE STATUS ===

backend_status = mgr.get_comprehensive_status("backend")
print(f"""
Backend Comprehensive Status:
- Total items: {backend_status['progress']['total']}
- Root items: {backend_status['progress']['root_items']} 
- Subtasks: {backend_status['progress']['subtasks']}
- Available to start: {backend_status['progress']['available']}
- Blocked: {backend_status['progress']['blocked']}
- Next recommended: {backend_status['next_task']['item_key'] if backend_status['next_task'] else 'None'}
""")

# === WORKFLOW SIMULATION ===

print("\n=== WORKFLOW SIMULATION ===")

# Step 1: Start backend auth models
mgr.update_item_status("backend", "models", "in_progress")
print("✅ Started: backend auth models")

# Check what's available now
backend_next = mgr.get_next_pending_with_subtasks("backend")
print(f"Backend next: {backend_next.item_key if backend_next else 'None'}")
# Expected: Still "models" (continue in-progress work)

# Step 2: Complete auth models
mgr.update_item_status("backend", "models", "completed")
print("✅ Completed: backend auth models")

# Check what's available now  
backend_next = mgr.get_next_pending_with_subtasks("backend")
print(f"Backend next: {backend_next.item_key if backend_next else 'None'}")
# Expected: "endpoints" (next subtask in auth)

# Step 3: Complete all auth subtasks
mgr.update_item_status("backend", "endpoints", "completed")
mgr.update_item_status("backend", "middleware", "completed") 

# Auth parent should auto-complete
auth_status = mgr.can_complete_item("backend", "auth")
print(f"Can complete auth parent: {auth_status['can_complete']}")

if auth_status['can_complete']:
    mgr.update_item_status("backend", "auth", "completed")
    print("✅ Auto-completed: backend auth system")

# Step 4: Check frontend availability
frontend_next = mgr.get_next_pending_with_subtasks("frontend")
print(f"Frontend next: {frontend_next.item_key if frontend_next else 'None'}")
# Expected: "auth_forms" (now unblocked!)

print("\n=== FINAL PROJECT STATUS ===")
project_progress = mgr.get_cross_list_progress("webapp")
for list_info in project_progress['lists']:
    progress = list_info['progress'] 
    print(f"{list_info['list']['title']}: {progress['completed']}/{progress['total']} completed ({progress['completion_percentage']:.1f}%)")
```

### Scenario 2: Software Release Pipeline

```python
"""
Complex software release with multiple teams and dependencies
"""

# === TEAM LISTS ===
mgr.create_list("dev", "Development Team")
mgr.create_list("qa", "QA Team") 
mgr.create_list("devops", "DevOps Team")
mgr.create_list("docs", "Documentation Team")

# === DEVELOPMENT PHASE ===
mgr.add_item("dev", "feature_a", "Feature A Implementation")
mgr.add_subtask("dev", "feature_a", "backend_api", "Backend API for Feature A")
mgr.add_subtask("dev", "feature_a", "frontend_ui", "Frontend UI for Feature A")
mgr.add_subtask("dev", "feature_a", "unit_tests", "Unit tests for Feature A")

mgr.add_item("dev", "feature_b", "Feature B Implementation")
mgr.add_subtask("dev", "feature_b", "core_logic", "Core business logic")
mgr.add_subtask("dev", "feature_b", "integration", "Integration with Feature A")
mgr.add_subtask("dev", "feature_b", "unit_tests", "Unit tests for Feature B")

# === QA PHASE ===
mgr.add_item("qa", "test_suite", "Test Suite Execution")
mgr.add_subtask("qa", "test_suite", "feature_a_tests", "Feature A testing")
mgr.add_subtask("qa", "test_suite", "feature_b_tests", "Feature B testing")  
mgr.add_subtask("qa", "test_suite", "integration_tests", "Integration testing")
mgr.add_subtask("qa", "test_suite", "regression_tests", "Regression testing")

mgr.add_item("qa", "performance", "Performance Testing")

# === DEVOPS PHASE ===
mgr.add_item("devops", "staging", "Staging Deployment")
mgr.add_item("devops", "monitoring", "Production Monitoring Setup")
mgr.add_item("devops", "production", "Production Deployment")

# === DOCUMENTATION PHASE ===
mgr.add_item("docs", "user_guide", "User Documentation")
mgr.add_item("docs", "api_docs", "API Documentation")
mgr.add_item("docs", "release_notes", "Release Notes")

# === CROSS-TEAM DEPENDENCIES ===

# QA depends on dev completion
mgr.add_item_dependency("qa", "feature_a_tests", "dev", "feature_a")
mgr.add_item_dependency("qa", "feature_b_tests", "dev", "feature_b")
mgr.add_item_dependency("qa", "integration_tests", "dev", "feature_a")
mgr.add_item_dependency("qa", "integration_tests", "dev", "feature_b")

# DevOps staging depends on QA
mgr.add_item_dependency("devops", "staging", "qa", "test_suite")

# DevOps production depends on staging and performance
mgr.add_item_dependency("devops", "production", "devops", "staging")
mgr.add_item_dependency("devops", "production", "qa", "performance")

# Docs depend on feature completion
mgr.add_item_dependency("docs", "api_docs", "dev", "feature_a")
mgr.add_item_dependency("docs", "api_docs", "dev", "feature_b")
mgr.add_item_dependency("docs", "release_notes", "devops", "production")

# === SMART COORDINATION ===

def print_team_status():
    """Print current status for all teams"""
    teams = ["dev", "qa", "devops", "docs"]
    
    print("\n=== TEAM STATUS ===")
    for team in teams:
        next_task = mgr.get_next_pending_with_subtasks(team)
        progress = mgr.get_progress(team) 
        
        print(f"{team.upper()}: {progress.completed}/{progress.total} completed")
        if next_task:
            print(f"  Next: {next_task.item_key} - {next_task.content}")
        else:
            if progress.blocked > 0:
                print(f"  Blocked: {progress.blocked} items waiting on dependencies")
            else:
                print(f"  Status: All tasks completed!")
        print()

# === RELEASE SIMULATION ===

print("=== RELEASE PIPELINE SIMULATION ===")

print_team_status()

# Development phase
print("🚀 Development Phase Starting...")
mgr.update_item_status("dev", "backend_api", "completed")
mgr.update_item_status("dev", "frontend_ui", "completed") 
mgr.update_item_status("dev", "unit_tests", "completed")
# Feature A auto-completes

print_team_status()

# QA can now start Feature A testing
print("🧪 QA Phase Starting...")
mgr.update_item_status("qa", "feature_a_tests", "completed")

# Continue development on Feature B
mgr.update_item_status("dev", "core_logic", "completed")
mgr.update_item_status("dev", "integration", "completed")
mgr.update_item_status("dev", "unit_tests", "completed")
# Feature B auto-completes

print_team_status()

# Complete QA phase
mgr.update_item_status("qa", "feature_b_tests", "completed")
mgr.update_item_status("qa", "integration_tests", "completed")
mgr.update_item_status("qa", "regression_tests", "completed")
# Test suite auto-completes

mgr.update_item_status("qa", "performance", "completed")

print_team_status()

# DevOps phase can now proceed
print("🚀 DevOps Phase Starting...")
mgr.update_item_status("devops", "staging", "completed")
mgr.update_item_status("devops", "monitoring", "completed")
mgr.update_item_status("devops", "production", "completed")

print_team_status()

# Documentation phase
print("📚 Documentation Phase...")
mgr.update_item_status("docs", "user_guide", "completed")
mgr.update_item_status("docs", "api_docs", "completed")
mgr.update_item_status("docs", "release_notes", "completed")

print_team_status()

print("🎉 Release Complete!")
```

### Scenario 3: Content Creation Pipeline

```python
"""
Content creation workflow with dependencies between writers, editors, and publishers
"""

# === CONTENT TEAM STRUCTURE ===
mgr.create_list("writing", "Content Writing")
mgr.create_list("editing", "Editorial Team")
mgr.create_list("design", "Design Team")
mgr.create_list("publishing", "Publishing Team")

# === WRITING TASKS ===
mgr.add_item("writing", "blog_series", "5-Part Blog Series")
mgr.add_subtask("writing", "blog_series", "part1", "Part 1: Introduction")
mgr.add_subtask("writing", "blog_series", "part2", "Part 2: Core Concepts")
mgr.add_subtask("writing", "blog_series", "part3", "Part 3: Advanced Topics")
mgr.add_subtask("writing", "blog_series", "part4", "Part 4: Case Studies") 
mgr.add_subtask("writing", "blog_series", "part5", "Part 5: Conclusion")

mgr.add_item("writing", "whitepaper", "Technical Whitepaper")
mgr.add_subtask("writing", "whitepaper", "research", "Research & Data Collection")
mgr.add_subtask("writing", "whitepaper", "draft", "First Draft")
mgr.add_subtask("writing", "whitepaper", "review", "Internal Review")

# === EDITING TASKS ===
mgr.add_item("editing", "blog_editing", "Blog Series Editing")
mgr.add_subtask("editing", "blog_editing", "copy_edit", "Copy Editing")
mgr.add_subtask("editing", "blog_editing", "fact_check", "Fact Checking")
mgr.add_subtask("editing", "blog_editing", "final_review", "Final Editorial Review")

mgr.add_item("editing", "whitepaper_editing", "Whitepaper Editing")

# === DESIGN TASKS ===
mgr.add_item("design", "blog_graphics", "Blog Graphics Package")
mgr.add_item("design", "whitepaper_layout", "Whitepaper Layout & Design")

# === PUBLISHING TASKS ===
mgr.add_item("publishing", "blog_schedule", "Blog Publishing Schedule")
mgr.add_item("publishing", "whitepaper_launch", "Whitepaper Launch Campaign")

# === CONTENT DEPENDENCIES ===

# Editing depends on writing completion
mgr.add_item_dependency("editing", "blog_editing", "writing", "blog_series")
mgr.add_item_dependency("editing", "whitepaper_editing", "writing", "whitepaper")

# Design can start once writing begins (parallel work)
mgr.add_item_dependency("design", "blog_graphics", "writing", "part1")  # Can start early
mgr.add_item_dependency("design", "whitepaper_layout", "writing", "draft")

# Publishing depends on both editing and design
mgr.add_item_dependency("publishing", "blog_schedule", "editing", "blog_editing")
mgr.add_item_dependency("publishing", "blog_schedule", "design", "blog_graphics")

mgr.add_item_dependency("publishing", "whitepaper_launch", "editing", "whitepaper_editing")
mgr.add_item_dependency("publishing", "whitepaper_launch", "design", "whitepaper_layout")

# === CONTENT WORKFLOW MANAGEMENT ===

def content_pipeline_status():
    """Show current content pipeline status"""
    print("\n=== CONTENT PIPELINE STATUS ===")
    
    teams = {
        "writing": "✍️ Writing Team",
        "editing": "✏️ Editorial Team", 
        "design": "🎨 Design Team",
        "publishing": "📢 Publishing Team"
    }
    
    for team_key, team_name in teams.items():
        status = mgr.get_comprehensive_status(team_key)
        progress = status['progress']
        
        print(f"\n{team_name}")
        print(f"  Progress: {progress['completed']}/{progress['total']} completed ({progress['completion_percentage']:.1f}%)")
        print(f"  Available: {progress['available']} | Blocked: {progress['blocked']}")
        
        if status['next_task']:
            print(f"  Next Task: {status['next_task']['item_key']} - {status['next_task']['content']}")
        elif progress['total'] > 0 and progress['completed'] == progress['total']:
            print(f"  ✅ All tasks completed!")
        else:
            print(f"  ⏸️ Waiting on dependencies")
            
        # Show blocked items
        if status['blocked_items']:
            print("  Blocked Items:")
            for item in status['blocked_items'][:3]:  # Show first 3
                print(f"    - {item['key']}: {item['reason']}")

content_pipeline_status()

# === WORKFLOW SIMULATION ===

print("\n🚀 Starting Content Creation Pipeline...")

# Writing team starts
mgr.update_item_status("writing", "part1", "completed")
print("✅ Blog Part 1 completed - Design team can now start graphics")

content_pipeline_status()

# Design starts in parallel
mgr.update_item_status("design", "blog_graphics", "in_progress")

# Continue writing
mgr.update_item_status("writing", "part2", "completed")
mgr.update_item_status("writing", "part3", "completed")
mgr.update_item_status("writing", "part4", "completed") 
mgr.update_item_status("writing", "part5", "completed")
# Blog series auto-completes

print("✅ Blog series writing completed - Editorial team unblocked")

content_pipeline_status()

# Editing can now proceed
mgr.update_item_status("editing", "copy_edit", "completed")
mgr.update_item_status("editing", "fact_check", "completed")
mgr.update_item_status("editing", "final_review", "completed")
# Blog editing auto-completes

# Complete design
mgr.update_item_status("design", "blog_graphics", "completed")

print("✅ Blog editing and design completed - Publishing team ready")

content_pipeline_status()

# Publishing phase
mgr.update_item_status("publishing", "blog_schedule", "completed")

print("✅ Blog series published!")

# Parallel whitepaper work
print("\n📄 Whitepaper workflow...")
mgr.update_item_status("writing", "research", "completed")
mgr.update_item_status("writing", "draft", "completed")

# Design can start
mgr.update_item_status("design", "whitepaper_layout", "in_progress")

mgr.update_item_status("writing", "review", "completed")
# Whitepaper auto-completes

mgr.update_item_status("editing", "whitepaper_editing", "completed")
mgr.update_item_status("design", "whitepaper_layout", "completed")
mgr.update_item_status("publishing", "whitepaper_launch", "completed")

content_pipeline_status()

print("\n🎉 Content creation pipeline completed!")
```

## 🎯 Key Takeaways

### Phase 1 Benefits (Subtasks)
- ✅ Natural task breakdown and hierarchy
- ✅ Smart prioritization of subtasks before parents
- ✅ Auto-completion of parents when all subtasks done

### Phase 2 Benefits (Cross-List Dependencies)  
- ✅ Coordination between teams/domains
- ✅ Prevents starting blocked work
- ✅ Clear dependency visualization

### Phase 3 Benefits (Integration)
- ✅ Intelligent task prioritization across all mechanisms
- ✅ Comprehensive progress tracking and visibility
- ✅ Unified API for complex workflows
- ✅ Scales from simple lists to complex multi-team projects

The Phase 3 system provides the foundation for any workflow complexity while maintaining simplicity for basic use cases.