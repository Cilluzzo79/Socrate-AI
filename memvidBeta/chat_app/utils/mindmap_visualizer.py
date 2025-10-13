"""
Interactive Mind Map Visualizer - Creates modern, interactive HTML mind maps with radial layout.
Features D3.js visualization, zoom/pan, search, and cyberpunk theme consistency.
"""

import json
import math
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


# Color palette for branches (matches outline theme)
BRANCH_COLORS = [
    '#FF6B6B',  # 1. Red/Orange
    '#4ECDC4',  # 2. Cyan  
    '#A855F7',  # 3. Purple
    '#3B82F6',  # 4. Blue
    '#F59E0B',  # 5. Amber/Yellow
    '#10B981',  # 6. Green
    '#EC4899',  # 7. Pink
]


def load_logo_base64() -> str:
    """Load logo from base64 file."""
    try:
        logo_path = Path(__file__).parent / "logo_base64.txt"
        if logo_path.exists():
            with open(logo_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        print(f"Warning: Could not load logo: {e}")
    return ""


def generate_dashboard_data(dashboard_data: Dict[str, Any]) -> str:
    """
    Convert dashboard data to web-ready format.
    
    Args:
        dashboard_data: Dictionary with dashboard structure
        
    Returns:
        JSON string for dashboard consumption
    """
    return json.dumps(dashboard_data)


def generate_mindmap_data_for_d3(mindmap_data: Dict[str, Any]) -> str:
    """
    Convert hierarchical mindmap data to D3.js compatible format with expandable nodes.
    
    Args:
        mindmap_data: Dictionary with 'central_concept' and 'branches' with sub_branches
        
    Returns:
        JSON string for D3.js consumption
    """
    central_concept = mindmap_data.get('central_concept', {})
    central_title = central_concept.get('title', 'Concetto Centrale') if isinstance(central_concept, dict) else str(central_concept)
    central_desc = central_concept.get('description', '') if isinstance(central_concept, dict) else ''
    
    branches = mindmap_data.get('branches', [])
    
    # Create nodes and links for D3.js with hierarchical structure
    nodes = [{
        'id': 'central',
        'name': central_title,
        'description': central_desc,
        'type': 'central',
        'level': 0,
        'color': '#06b6d4',
        'size': 80,
        'expanded': True,
        'visible': True
    }]
    
    links = []
    
    # Add branch nodes (level 1)
    for i, branch in enumerate(branches):
        branch_id = f'branch_{i}'
        branch_color = BRANCH_COLORS[i % len(BRANCH_COLORS)]
        
        nodes.append({
            'id': branch_id,
            'name': branch.get('title', f'Ramo {i+1}'),
            'description': branch.get('description', ''),
            'type': 'branch',
            'level': 1,
            'color': branch_color,
            'size': 50,
            'branchIndex': i,
            'expanded': branch.get('expanded', False),
            'visible': True,
            'hasChildren': len(branch.get('sub_branches', [])) > 0
        })
        
        links.append({
            'source': 'central',
            'target': branch_id,
            'type': 'branch-link'
        })
        
        # Add sub-branch nodes (level 2)
        sub_branches = branch.get('sub_branches', [])
        for j, sub_branch in enumerate(sub_branches):
            sub_branch_id = f'sub_branch_{i}_{j}'
            
            nodes.append({
                'id': sub_branch_id,
                'name': sub_branch.get('title', f'Sotto-ramo {j+1}'),
                'description': sub_branch.get('description', ''),
                'type': 'sub_branch',
                'level': 2,
                'color': branch_color,
                'size': 40,
                'branchIndex': i,
                'subBranchIndex': j,
                'expanded': sub_branch.get('expanded', False),
                'visible': branch.get('expanded', False),  # Visible only if parent is expanded
                'hasChildren': len(sub_branch.get('nodes', [])) > 0,
                'parentId': branch_id
            })
            
            links.append({
                'source': branch_id,
                'target': sub_branch_id,
                'type': 'sub-branch-link'
            })
            
            # Add detail nodes (level 3)
            nodes_list = sub_branch.get('nodes', [])
            for k, node in enumerate(nodes_list):
                node_id = f'node_{i}_{j}_{k}'
                
                nodes.append({
                    'id': node_id,
                    'name': node.get('title', f'Nodo {k+1}'),
                    'description': node.get('description', ''),
                    'type': 'node',
                    'level': 3,
                    'color': branch_color,
                    'size': 30,
                    'branchIndex': i,
                    'subBranchIndex': j,
                    'nodeIndex': k,
                    'expanded': False,
                    'visible': sub_branch.get('expanded', False),  # Visible only if parent is expanded
                    'hasChildren': False,
                    'parentId': sub_branch_id
                })
                
                links.append({
                    'source': sub_branch_id,
                    'target': node_id,
                    'type': 'node-link'
                })
        
        # Legacy support: if no sub_branches, use old 'nodes' structure
        if not sub_branches:
            for j, node in enumerate(branch.get('nodes', [])):
                node_id = f'node_{i}_{j}'
                
                nodes.append({
                    'id': node_id,
                    'name': node.get('title', f'Nodo {j+1}'),
                    'description': node.get('description', ''),
                    'type': 'node',
                    'level': 2,
                    'color': branch_color,
                    'size': 35,
                    'branchIndex': i,
                    'nodeIndex': j,
                    'expanded': False,
                    'visible': True,
                    'hasChildren': False,
                    'parentId': branch_id
                })
                
                links.append({
                    'source': branch_id,
                    'target': node_id,
                    'type': 'node-link'
                })
    
    return json.dumps({'nodes': nodes, 'links': links})


def generate_study_dashboard_html(
    dashboard_data: Dict[str, Any],
    document_title: str = "Dashboard di Studio",
    metadata: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate professional study dashboard HTML.
    
    Args:
        dashboard_data: Dictionary with dashboard structure
        document_title: Title of the document
        metadata: Optional metadata dictionary
        
    Returns:
        Complete HTML string with dashboard interface
    """
    
    # Load logo
    logo_base64 = load_logo_base64()
    
    # Build metadata HTML
    metadata_html = ""
    if metadata:
        metadata_items = []
        for key, value in metadata.items():
            icon = {
                'Documento': '📄',
                'Complessità': '🎯',
                'Concetti': '💡',
                'Sezioni': '📊',
                'Collegamenti': '🔗',
                'Tempo generazione': '⏱️'
            }.get(key, '📌')
            
            metadata_items.append(f"""
                <div class="metadata-item">
                    <span class="metadata-icon">{icon}</span>
                    <span class="metadata-label">{key}:</span>
                    <span class="metadata-value">{value}</span>
                </div>
            """)
        
        metadata_html = f"""
            <div class="metadata-box">
                {''.join(metadata_items)}
            </div>
        """
    
    # Process dashboard data
    doc_info = dashboard_data.get('document_info', {})
    key_concepts = dashboard_data.get('key_concepts', [])
    structural_map = dashboard_data.get('structural_map', [])
    connections = dashboard_data.get('connections', [])
    key_excerpts = dashboard_data.get('key_excerpts', [])
    logical_progression = dashboard_data.get('logical_progression', [])
    
    # Convert to JSON for JavaScript
    dashboard_json = generate_dashboard_data(dashboard_data)
    
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{document_title} - Dashboard di Studio</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #1e40af;
            --accent-color: #06b6d4;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --bg-dark: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: #475569;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        
        body {{
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
            padding: 40px 30px;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 100%;
            background: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(255, 255, 255, 0.05) 10px,
                rgba(255, 255, 255, 0.05) 20px
            );
            pointer-events: none;
        }}
        
        .logo {{
            margin-bottom: 20px;
        }}
        
        .logo-img {{
            max-width: 200px;
            height: auto;
            filter: drop-shadow(0 0 15px rgba(255, 255, 255, 0.3));
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
            margin-bottom: 10px;
            position: relative;
        }}
        
        .header .subtitle {{
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.9);
            position: relative;
        }}
        
        /* Metadata */
        .metadata-box {{
            background: var(--bg-tertiary);
            border: 2px solid var(--accent-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
            box-shadow: var(--shadow);
        }}
        
        .metadata-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .metadata-icon {{
            font-size: 1.2rem;
        }}
        
        .metadata-label {{
            color: var(--accent-color);
            font-weight: 600;
        }}
        
        .metadata-value {{
            color: var(--text-primary);
            font-weight: 500;
        }}
        
        /* Dashboard Grid */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: auto auto;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .dashboard-section {{
            background: var(--bg-secondary);
            border-radius: 16px;
            padding: 30px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border-color);
        }}
        
        .section-icon {{
            font-size: 1.5rem;
        }}
        
        .section-title {{
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        
        /* Key Concepts */
        .concepts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }}
        
        .concept-card {{
            background: var(--bg-tertiary);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .concept-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }}
        
        .concept-card.high {{ border-left-color: var(--danger-color); }}
        .concept-card.medium {{ border-left-color: var(--warning-color); }}
        .concept-card.low {{ border-left-color: var(--success-color); }}
        
        .concept-title {{
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 8px;
            color: var(--text-primary);
        }}
        
        .concept-description {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        
        .concept-category {{
            position: absolute;
            top: 12px;
            right: 12px;
            background: var(--accent-color);
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        
        /* Structural Map */
        .structural-tree {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .tree-node {{
            margin-bottom: 8px;
        }}
        
        .tree-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px;
            background: var(--bg-tertiary);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .tree-item:hover {{
            background: var(--border-color);
        }}
        
        .tree-level-1 {{ margin-left: 0; }}
        .tree-level-2 {{ margin-left: 24px; }}
        .tree-level-3 {{ margin-left: 48px; }}
        .tree-level-4 {{ margin-left: 72px; }}
        
        .tree-icon {{
            font-size: 1rem;
            color: var(--accent-color);
        }}
        
        .tree-title {{
            font-weight: 500;
            color: var(--text-primary);
        }}
        
        .tree-description {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 4px;
        }}
        
        /* Connections Network */
        .connections-container {{
            position: relative;
            height: 300px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            overflow: hidden;
        }}
        
        .connection-node {{
            position: absolute;
            background: var(--accent-color);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .connection-node:hover {{
            transform: scale(1.1);
            box-shadow: 0 0 15px var(--accent-color);
        }}
        
        /* Key Excerpts */
        .excerpts-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .excerpt-item {{
            background: var(--bg-tertiary);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid var(--accent-color);
        }}
        
        .excerpt-text {{
            font-style: italic;
            color: var(--text-primary);
            margin-bottom: 12px;
            font-size: 1rem;
            line-height: 1.6;
        }}
        
        .excerpt-context {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        /* Logical Progression Styles */
        .progression-step {{
            display: flex;
            align-items: flex-start;
            background: var(--bg-tertiary);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            border-left: 4px solid var(--success-color);
        }}
        
        .step-number {{
            background: var(--success-color);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2rem;
            margin-right: 16px;
            flex-shrink: 0;
        }}
        
        .step-content {{
            flex: 1;
        }}
        
        .step-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }}
        
        .step-description {{
            color: var(--text-muted);
            line-height: 1.5;
        }}
        
        /* Controls */
        .controls-panel {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
        }}
        
        .control-button {{
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .control-button:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        /* Search */
        .search-container {{
            position: relative;
            flex-grow: 1;
            max-width: 400px;
        }}
        
        .search-input {{
            width: 100%;
            padding: 12px 16px;
            background: var(--bg-dark);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            margin-top: 40px;
        }}
        
        /* Responsive */
        @media (max-width: 1024px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .header {{ padding: 30px 20px; }}
            .dashboard-section {{ padding: 20px; }}
            .concepts-grid {{ grid-template-columns: 1fr; }}
        }}
        
        /* Print styles */
        @media print {{
            body {{ background: white; color: black; }}
            .controls-panel {{ display: none; }}
            .dashboard-section {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            {f'<div class="logo"><img src="data:image/png;base64,{logo_base64}" alt="Socrate AI" class="logo-img"></div>' if logo_base64 else ''}
            <h1>📚 Socrate AI</h1>
            <h2>{document_title}</h2>
            <div class="subtitle">Dashboard di Studio Professionale</div>
        </div>
        
        <!-- Metadata -->
        {metadata_html}
        
        <!-- Controls -->
        <div class="controls-panel">
            <div class="search-container">
                <input type="text" class="search-input" id="search-input" placeholder="Cerca concetti, sezioni, estratti...">
            </div>
            <button class="control-button" onclick="exportPDF()">📄 Esporta PDF</button>
            <button class="control-button" onclick="toggleView()">🔄 Cambia Vista</button>
            <button class="control-button" onclick="generateQuiz()">🎓 Quiz</button>
        </div>
        
        <!-- Dashboard Grid -->
        <div class="dashboard-grid">
            <!-- Key Concepts -->
            <div class="dashboard-section">
                <div class="section-header">
                    <span class="section-icon">💡</span>
                    <h3 class="section-title">Concetti Chiave</h3>
                </div>
                <div class="concepts-grid" id="concepts-container">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
            
            <!-- Structural Map -->
            <div class="dashboard-section">
                <div class="section-header">
                    <span class="section-icon">📊</span>
                    <h3 class="section-title">Mappa Strutturale</h3>
                </div>
                <div class="structural-tree" id="structural-container">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
            
            <!-- Connections -->
            <div class="dashboard-section">
                <div class="section-header">
                    <span class="section-icon">🔗</span>
                    <h3 class="section-title">Collegamenti</h3>
                </div>
                <div class="connections-container" id="connections-container">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
            
            <!-- Key Excerpts -->
            <div class="dashboard-section">
                <div class="section-header">
                    <span class="section-icon">📝</span>
                    <h3 class="section-title">Estratti Chiave</h3>
                </div>
                <div class="excerpts-list" id="excerpts-container">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
            
            <!-- Logical Progression -->
            <div class="dashboard-section">
                <div class="section-header">
                    <span class="section-icon">🔄</span>
                    <h3 class="section-title">Progressione Logica</h3>
                </div>
                <div class="progression-list" id="progression-container">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')} •
            Dashboard di Studio by 🤖 Socrate AI • Powered by Claude Sonnet 4.5
        </div>
    </div>
    
    <script>
        // Dashboard data
        const dashboardData = {dashboard_json};
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            initializeDashboard();
        }});
        
        function initializeDashboard() {{
            populateKeyConcepts();
            populateStructuralMap();
            populateConnections();
            populateExcerpts();
            populateLogicalProgression();
            setupSearch();
        }}
        
        function populateKeyConcepts() {{
            const container = document.getElementById('concepts-container');
            const concepts = dashboardData.key_concepts || [];
            
            container.innerHTML = concepts.map(concept => {{
                return `
                    <div class="concept-card ${{concept.importance}}" onclick="focusConcept('${{concept.id}}')">
                        <div class="concept-category">${{concept.category || 'Generale'}}</div>
                        <div class="concept-title">${{concept.title}}</div>
                        <div class="concept-description">${{concept.description}}</div>
                    </div>
                `;
            }}).join('');
        }}
        
        function populateStructuralMap() {{
            const container = document.getElementById('structural-container');
            const sections = dashboardData.structural_map || [];
            
            let html = '';
            sections.forEach(section => {{
                html += renderTreeNode(section);
            }});
            container.innerHTML = html;
        }}
        
        function renderTreeNode(node) {{
            let html = `
                <div class="tree-node">
                    <div class="tree-item tree-level-${{node.level}}" onclick="expandSection('${{node.id}}')">
                        <span class="tree-icon">${{node.level === 1 ? '📁' : '📄'}}</span>
                        <div>
                            <div class="tree-title">${{node.title}}</div>
                            <div class="tree-description">${{node.description}}</div>
                        </div>
                    </div>
                </div>
            `;
            
            if (node.subsections) {{
                node.subsections.forEach(sub => {{
                    html += renderTreeNode(sub);
                }});
            }}
            
            return html;
        }}
        
        function populateConnections() {{
            const container = document.getElementById('connections-container');
            const connections = dashboardData.connections || [];
            
            // Simple network visualization
            connections.forEach((conn, index) => {{
                const x = 50 + (index % 3) * 120;
                const y = 50 + Math.floor(index / 3) * 80;
                
                const node = document.createElement('div');
                node.className = 'connection-node';
                node.style.left = x + 'px';
                node.style.top = y + 'px';
                node.textContent = conn.from + ' → ' + conn.to;
                node.title = conn.description;
                container.appendChild(node);
            }});
        }}
        
        function populateExcerpts() {{
            const container = document.getElementById('excerpts-container');
            const excerpts = dashboardData.key_excerpts || [];
            
            container.innerHTML = excerpts.map(excerpt => {{
                return `
                    <div class="excerpt-item">
                        <div class="excerpt-text">"${{excerpt.text}}"</div>
                        <div class="excerpt-context">${{excerpt.context}}</div>
                    </div>
                `;
            }}).join('');
        }}
        
        function populateLogicalProgression() {{
            const container = document.getElementById('progression-container');
            const progression = dashboardData.logical_progression || [];
            
            container.innerHTML = progression.map(step => {{
                return `
                    <div class="progression-step">
                        <div class="step-number">${{step.step}}</div>
                        <div class="step-content">
                            <div class="step-title">${{step.title}}</div>
                            <div class="step-description">${{step.description}}</div>
                        </div>
                    </div>
                `;
            }}).join('');
        }}
        
        function setupSearch() {{
            const searchInput = document.getElementById('search-input');
            searchInput.addEventListener('input', function(e) {{
                const query = e.target.value.toLowerCase();
                filterContent(query);
            }});
        }}
        
        function filterContent(query) {{
            // Filter concepts
            document.querySelectorAll('.concept-card').forEach(card => {{
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(query) ? 'block' : 'none';
            }});
            
            // Filter tree items
            document.querySelectorAll('.tree-item').forEach(item => {{
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? 'flex' : 'none';
            }});
            
            // Filter excerpts
            document.querySelectorAll('.excerpt-item').forEach(item => {{
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? 'block' : 'none';
            }});
            
            // Filter progression steps
            document.querySelectorAll('.progression-step').forEach(item => {{
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? 'flex' : 'none';
            }});
        }}
        
        function focusConcept(conceptId) {{
            alert('Focus su concetto: ' + conceptId);
        }}
        
        function expandSection(sectionId) {{
            alert('Espandi sezione: ' + sectionId);
        }}
        
        function exportPDF() {{
            window.print();
        }}
        
        function toggleView() {{
            alert('Funzionalità cambio vista in sviluppo');
        }}
        
        function generateQuiz() {{
            alert('Generazione quiz in sviluppo');
        }}
    </script>
</body>
</html>"""
    
    return html


def generate_mindmap_html(
    mindmap_data: Dict[str, Any],
    document_title: str = "Mappa Concettuale",
    metadata: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate interactive HTML mind map with modern radial layout using D3.js.
    
    Args:
        mindmap_data: Dictionary with 'central_concept' and 'branches'
        document_title: Title of the document
        metadata: Optional metadata dictionary
        
    Returns:
        Complete HTML string with embedded CSS and JavaScript
    """
    
    central_concept = mindmap_data.get('central_concept', {})
    central_title = central_concept.get('title', 'Concetto Centrale') if isinstance(central_concept, dict) else str(central_concept)
    branches = mindmap_data.get('branches', [])
    
    # Generate D3.js data
    d3_data = generate_mindmap_data_for_d3(mindmap_data)
    
    # Load logo
    logo_base64 = load_logo_base64()
    
    # Build metadata HTML
    metadata_html = ""
    if metadata:
        metadata_items = []
        for key, value in metadata.items():
            icon = {
                'Tipo': '📋',
                'Profondità': '🔍',
                'Livelli': '🌳',
                'Tempo generazione': '⏱️',
                'Documento': '📄',
                'Rami': '🌿',
                'Nodi totali': '🔢'
            }.get(key, '📌')
            
            metadata_items.append(f"""
                <div class="metadata-item">
                    <span class="metadata-icon">{icon}</span>
                    <span class="metadata-label">{key}:</span>
                    <span class="metadata-value">{value}</span>
                </div>
            """)
        
        metadata_html = f"""
            <div class="metadata-box">
                {''.join(metadata_items)}
            </div>
        """
    
    # Count stats
    total_nodes = sum(len(b.get('nodes', [])) for b in branches)
    num_branches = len(branches)
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{document_title} - Mappa Concettuale</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --neon-cyan: #06b6d4;
            --neon-purple: #a855f7;
            --neon-pink: #ec4899;
            --bg-dark: #0a0a0f;
            --bg-secondary: #1a1a2e;
            --bg-tertiary: #16213e;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --border-color: #2d3748;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* Header with logo */
        .header {{
            background: linear-gradient(135deg, var(--neon-purple) 0%, var(--neon-cyan) 100%);
            padding: 40px 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(6, 182, 212, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 0, 0, 0.1) 2px,
                rgba(0, 0, 0, 0.1) 4px
            );
            pointer-events: none;
            animation: scanlines 10s linear infinite;
        }}
        
        @keyframes scanlines {{
            0% {{ transform: translateY(0); }}
            100% {{ transform: translateY(20px); }}
        }}
        
        .logo {{
            margin-bottom: 20px;
        }}
        
        .logo-img {{
            max-width: 250px;
            height: auto;
            filter: drop-shadow(0 0 20px rgba(6, 182, 212, 0.6));
            animation: float 3s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        .header h1 {{
            font-size: 2.5em;
            color: white;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
            margin-bottom: 10px;
            position: relative;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            color: rgba(255, 255, 255, 0.9);
            position: relative;
        }}
        
        /* Metadata box */
        .metadata-box {{
            background: var(--bg-tertiary);
            border: 2px solid var(--neon-cyan);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
            box-shadow: 0 0 30px rgba(6, 182, 212, 0.2);
            animation: pulse-border 2s ease-in-out infinite;
        }}
        
        @keyframes pulse-border {{
            0%, 100% {{ box-shadow: 0 0 30px rgba(6, 182, 212, 0.2); }}
            50% {{ box-shadow: 0 0 40px rgba(6, 182, 212, 0.4); }}
        }}
        
        .metadata-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .metadata-icon {{
            font-size: 1.3em;
        }}
        
        .metadata-label {{
            color: var(--neon-cyan);
            font-weight: 600;
        }}
        
        .metadata-value {{
            color: var(--text-primary);
        }}
        
        /* Controls panel */
        .controls-panel {{
            background: var(--bg-tertiary);
            border: 2px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
            justify-content: space-between;
        }}
        
        .search-container {{
            position: relative;
            flex-grow: 1;
            min-width: 250px;
        }}
        
        .search-input {{
            width: 100%;
            padding: 12px 45px 12px 15px;
            background: var(--bg-dark);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1em;
            transition: all 0.3s ease;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: var(--neon-cyan);
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
        }}
        
        .search-icon {{
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            font-size: 1.2em;
        }}
        
        .control-button {{
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 0.95em;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            box-shadow: 0 3px 10px rgba(6, 182, 212, 0.3);
        }}
        
        .control-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(6, 182, 212, 0.5);
        }}
        
        .view-mode-toggle {{
            display: flex;
            background: var(--bg-dark);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .view-mode-button {{
            background: transparent;
            color: var(--text-secondary);
            border: none;
            padding: 10px 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .view-mode-button.active {{
            background: var(--neon-cyan);
            color: white;
        }}
        
        /* Mind map container */
        .mindmap-container {{
            background: var(--bg-tertiary);
            border-radius: 15px;
            border: 2px solid var(--border-color);
            margin-bottom: 30px;
            position: relative;
            overflow: hidden;
            height: 700px;
        }}
        
        .mindmap-svg {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        
        .mindmap-svg:active {{
            cursor: grabbing;
        }}
        
        /* Node styles */
        .node-central {{
            filter: drop-shadow(0 0 10px var(--neon-cyan));
        }}
        
        .node-branch {{
            filter: drop-shadow(0 0 5px rgba(0, 0, 0, 0.5));
            cursor: pointer;
        }}
        
        .node-sub_branch {{
            filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.4));
            cursor: pointer;
        }}
        
        .node-node {{
            filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.3));
            cursor: pointer;
        }}
        
        /* Expandable node indicators */
        .node-expandable {{
            stroke-width: 3;
            stroke-dasharray: 5,5;
            animation: expandable-pulse 2s ease-in-out infinite;
        }}
        
        @keyframes expandable-pulse {{
            0%, 100% {{ stroke-opacity: 0.6; }}
            50% {{ stroke-opacity: 1; }}
        }}
        
        .node-expanded {{
            stroke-width: 4;
            stroke: var(--neon-cyan);
        }}
        
        .node-collapsed {{
            stroke-width: 2;
            stroke: var(--text-secondary);
        }}
        
        /* Hidden nodes */
        .node-hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .link-hidden {{
            opacity: 0;
        }}
        
        .node-text {{
            font-family: 'Segoe UI', sans-serif;
            font-weight: 600;
            text-anchor: middle;
            dominant-baseline: middle;
            pointer-events: none;
        }}
        
        .link {{
            stroke-width: 2;
            fill: none;
            opacity: 0.8;
        }}
        
        .link-branch {{
            stroke: var(--neon-cyan);
            stroke-width: 3;
        }}
        
        .link-node {{
            stroke-width: 2;
        }}
        
        /* Tooltip */
        .tooltip {{
            position: absolute;
            background: var(--bg-dark);
            border: 2px solid var(--neon-cyan);
            border-radius: 8px;
            padding: 15px;
            color: var(--text-primary);
            font-size: 0.9em;
            max-width: 300px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 1000;
        }}
        
        .tooltip.visible {{
            opacity: 1;
        }}
        
        .tooltip-title {{
            font-weight: bold;
            color: var(--neon-cyan);
            margin-bottom: 8px;
        }}
        
        .tooltip-description {{
            color: var(--text-secondary);
            line-height: 1.4;
        }}
        
        /* Legend */
        .legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--bg-dark);
            border: 2px solid var(--border-color);
            border-radius: 10px;
            padding: 15px;
            font-size: 0.85em;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
        }}
        
        /* Export panel */
        .export-panel {{
            background: var(--bg-tertiary);
            border: 2px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .export-buttons {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 20px;
            color: var(--text-secondary);
            font-size: 0.95em;
            border-top: 1px solid var(--border-color);
            margin-top: 40px;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .controls-panel {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .search-container {{
                min-width: auto;
            }}
            
            .mindmap-container {{
                height: 500px;
            }}
            
            .legend {{
                position: relative;
                top: auto;
                right: auto;
                margin-bottom: 20px;
            }}
        }}
        
        /* Print styles */
        @media print {{
            body {{
                background: white;
                color: black;
            }}
            
            .controls-panel, .export-panel {{
                display: none;
            }}
            
            .mindmap-container {{
                border: 1px solid black;
                height: auto;
                min-height: 600px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header with logo -->
        <div class="header">
            {f'<div class="logo"><img src="data:image/png;base64,{logo_base64}" alt="Socrate AI" class="logo-img"></div>' if logo_base64 else ''}
            <h1>💻 Socrate AI</h1>
            <h2>🧠 {document_title}</h2>
            <div class="subtitle">Mappa Concettuale Interattiva • Memvid Chat System</div>
        </div>
        
        <!-- Metadata -->
        {metadata_html}
        
        <!-- Controls Panel -->
        <div class="controls-panel">
            <div class="search-container">
                <input type="text" class="search-input" id="search-input" placeholder="Cerca nodi, rami o concetti...">
                <span class="search-icon">🔍</span>
            </div>
            
            <div class="view-mode-toggle">
                <button class="view-mode-button active" data-mode="radial">🌟 Radiale</button>
                <button class="view-mode-button" data-mode="tree">🌳 Albero</button>
            </div>
            
            <button class="control-button" onclick="resetView()">🎯 Reset Vista</button>
            <button class="control-button" onclick="fitToScreen()">📱 Adatta</button>
        </div>
        
        <!-- Mind Map Container -->
        <div class="mindmap-container">
            <svg class="mindmap-svg" id="mindmap-svg"></svg>
            
            <!-- Legend -->
            <div class="legend" id="legend">
                <div style="font-weight: bold; margin-bottom: 10px; color: var(--neon-cyan);">🗺️ Legenda</div>
                <div class="legend-item">
                    <div class="legend-color" style="background: var(--neon-cyan);"></div>
                    <span>Concetto Centrale</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #FF6B6B;"></div>
                    <span>Rami Principali</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4ECDC4;"></div>
                    <span>Nodi Dettaglio</span>
                </div>
            </div>
            
            <!-- Tooltip -->
            <div class="tooltip" id="tooltip">
                <div class="tooltip-title" id="tooltip-title"></div>
                <div class="tooltip-description" id="tooltip-description"></div>
            </div>
        </div>
        
        <!-- Export Panel -->
        <div class="export-panel">
            <h3 style="margin-bottom: 15px; color: var(--neon-cyan);">📤 Esporta Mappa</h3>
            <div class="export-buttons">
                <button class="control-button" onclick="exportHTML()">💾 HTML</button>
                <button class="control-button" onclick="exportPDF()">📄 PDF</button>
                <button class="control-button" onclick="exportPNG()">🖼️ PNG</button>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')} •
            Creato con 🤖 Socrate AI • Powered by Claude Sonnet 4.5
        </div>
    </div>
    
    <script>
        // Mind map data
        const mindmapData = {d3_data};
        
        // SVG dimensions and setup
        const svg = d3.select("#mindmap-svg");
        const width = 1200;
        const height = 700;
        
        svg.attr("viewBox", [0, 0, width, height]);
        
        // Create groups for different elements
        const g = svg.append("g");
        const linksGroup = g.append("g").attr("class", "links");
        const nodesGroup = g.append("g").attr("class", "nodes");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        // Force simulation
        let simulation;
        let currentMode = 'radial';
        
        // Initialize the mind map
        function initMindMap() {{
            const {{ nodes, links }} = mindmapData;
            
            // Create simulation
            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id).distance(d => {{
                    if (d.source.type === 'central') return 250;
                    if (d.source.type === 'branch') return 150;
                    return 100;
                }}))
                .force("charge", d3.forceManyBody().strength(d => {{
                    if (d.type === 'central') return -800;
                    if (d.type === 'branch') return -400;
                    return -200;
                }}))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide(d => d.size + 20));
            
            // Create links
            const link = linksGroup
                .selectAll("path")
                .data(links)
                .join("path")
                .attr("class", d => `link link-${{d.type.replace('-link', '')}}`)
                .attr("stroke", d => {{
                    if (d.type === 'branch-link') return '#06b6d4';
                    return d.source.color || '#94a3b8';
                }});
            
            // Create nodes
            const node = nodesGroup
                .selectAll("g")
                .data(nodes)
                .join("g")
                .attr("class", d => `node-${{d.type}}`)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            // Add circles to nodes
            node.append("circle")
                .attr("r", d => d.size)
                .attr("fill", d => d.color)
                .attr("stroke", d => {{
                    if (d.type === 'central') return '#ffffff';
                    return d.color;
                }})
                .attr("stroke-width", d => {{
                    if (d.type === 'central') return 4;
                    if (d.hasChildren && d.expanded) return 3;
                    if (d.hasChildren) return 2;
                    return 1;
                }})
                .attr("class", d => {{
                    let classes = [];
                    if (d.hasChildren) classes.push('node-expandable');
                    if (d.expanded) classes.push('node-expanded');
                    if (!d.visible) classes.push('node-hidden');
                    return classes.join(' ');
                }});
            
            // Add text to nodes
            node.append("text")
                .attr("class", "node-text")
                .attr("fill", d => d.type === 'central' ? '#ffffff' : '#ffffff')
                .attr("font-size", d => {{
                    if (d.type === 'central') return '18px';
                    if (d.type === 'branch') return '14px';
                    return '12px';
                }})
                .text(d => {{
                    if (d.type === 'central') {{
                        if (d.name.length > 30) return d.name.substring(0, 30) + '...';
                        return d.name;
                    }} else if (d.type === 'branch') {{
                        if (d.name.length > 25) return d.name.substring(0, 25) + '...';
                        return d.name;
                    }} else {{
                        if (d.name.length > 22) return d.name.substring(0, 22) + '...';
                        return d.name;
                    }}
                }});
            
            // Add hover effects and click handlers
            node
                .on("mouseenter", showTooltip)
                .on("mouseleave", hideTooltip)
                .on("click", (event, d) => {{
                    event.stopPropagation();
                    if (d.hasChildren) {{
                        toggleNode(d);
                    }} else {{
                        focusNode(event, d);
                    }}
                }});
            
            // Update positions on simulation tick
            simulation.on("tick", () => {{
                link.attr("d", d => {{
                    const dx = d.target.x - d.source.x;
                    const dy = d.target.y - d.source.y;
                    const dr = Math.sqrt(dx * dx + dy * dy) * 0.3;
                    return `M${{d.source.x}},${{d.source.y}}A${{dr}},${{dr}} 0 0,1 ${{d.target.x}},${{d.target.y}}`;
                }});
                
                node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            }});
        }}
        
        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        // Tooltip functions
        function showTooltip(event, d) {{
            const tooltip = document.getElementById('tooltip');
            const titleEl = document.getElementById('tooltip-title');
            const descEl = document.getElementById('tooltip-description');
            
            titleEl.textContent = d.name;
            descEl.textContent = d.description || 'Nessuna descrizione disponibile';
            
            tooltip.style.left = (event.pageX + 15) + 'px';
            tooltip.style.top = (event.pageY - 15) + 'px';
            tooltip.classList.add('visible');
        }}
        
        function hideTooltip() {{
            document.getElementById('tooltip').classList.remove('visible');
        }}
        
        // Toggle node expansion
        function toggleNode(d) {{
            d.expanded = !d.expanded;
            
            // Update visibility of children
            updateNodeVisibility();
            
            // Update visual styles
            updateNodeStyles();
            
            // Restart simulation with updated data
            simulation.alpha(0.3).restart();
        }}
        
        // Update visibility of all nodes based on their parents' expanded state
        function updateNodeVisibility() {{
            const {{ nodes, links }} = mindmapData;
            
            nodes.forEach(node => {{
                if (node.type === 'central') {{
                    node.visible = true;
                }} else if (node.parentId) {{
                    const parent = nodes.find(n => n.id === node.parentId);
                    node.visible = parent ? parent.expanded && parent.visible : false;
                }} else {{
                    node.visible = true; // Top-level branches
                }}
            }});
            
            // Update link visibility
            links.forEach(link => {{
                const sourceNode = nodes.find(n => n.id === link.source.id || n.id === link.source);
                const targetNode = nodes.find(n => n.id === link.target.id || n.id === link.target);
                link.visible = sourceNode && targetNode && sourceNode.visible && targetNode.visible;
            }});
        }}
        
        // Update visual styles of nodes
        function updateNodeStyles() {{
            nodesGroup.selectAll('g')
                .style('opacity', d => d.visible ? 1 : 0)
                .style('pointer-events', d => d.visible ? 'all' : 'none');
            
            nodesGroup.selectAll('circle')
                .attr("stroke-width", d => {{
                    if (d.type === 'central') return 4;
                    if (d.hasChildren && d.expanded) return 3;
                    if (d.hasChildren) return 2;
                    return 1;
                }})
                .attr("class", d => {{
                    let classes = [];
                    if (d.hasChildren) classes.push('node-expandable');
                    if (d.expanded) classes.push('node-expanded');
                    if (!d.visible) classes.push('node-hidden');
                    return classes.join(' ');
                }});
            
            linksGroup.selectAll('path')
                .style('opacity', d => d.visible ? 0.8 : 0);
        }}
        
        // Focus on specific node
        function focusNode(event, d) {{
            if (!d.visible) return;
            
            const transform = d3.zoomIdentity
                .translate(width / 2 - d.x, height / 2 - d.y)
                .scale(1.5);
            
            svg.transition()
                .duration(750)
                .call(zoom.transform, transform);
        }}
        
        // Control functions
        function resetView() {{
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity);
        }}
        
        function fitToScreen() {{
            const bounds = g.node().getBBox();
            const fullWidth = width;
            const fullHeight = height;
            const scale = Math.min(fullWidth / bounds.width, fullHeight / bounds.height) * 0.8;
            const translate = [fullWidth / 2 - scale * (bounds.x + bounds.width / 2), 
                            fullHeight / 2 - scale * (bounds.y + bounds.height / 2)];
            
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        }}
        
        // Search functionality
        document.getElementById('search-input').addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();
            
            nodesGroup.selectAll('g')
                .style('opacity', d => {{
                    if (!searchTerm) return 1;
                    return d.name.toLowerCase().includes(searchTerm) || 
                           (d.description && d.description.toLowerCase().includes(searchTerm)) ? 1 : 0.3;
                }});
        }});
        
        // View mode toggle
        document.querySelectorAll('.view-mode-button').forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                document.querySelectorAll('.view-mode-button').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                
                const mode = e.target.dataset.mode;
                switchViewMode(mode);
            }});
        }});
        
        function switchViewMode(mode) {{
            currentMode = mode;
            
            if (mode === 'tree') {{
                // Tree layout
                simulation.force("radial", null);
                simulation.force("x", d3.forceX(width / 2).strength(0.1));
                simulation.force("y", d3.forceY(d => d.level * 150 + 100).strength(0.8));
            }} else {{
                // Radial layout
                simulation.force("x", null);
                simulation.force("y", null);
                simulation.force("radial", d3.forceRadial(d => d.level * 180, width / 2, height / 2).strength(0.8));
            }}
            
            simulation.alpha(0.3).restart();
        }}
        
        // Export functions
        function exportHTML() {{
            const htmlContent = document.documentElement.outerHTML;
            const blob = new Blob([htmlContent], {{ type: 'text/html' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{document_title.replace(" ", "_")}_mindmap.html';
            a.click();
            URL.revokeObjectURL(url);
        }}
        
        function exportPDF() {{
            window.print();
        }}
        
        function exportPNG() {{
            // Create a canvas and render the SVG
            const svgElement = document.getElementById('mindmap-svg');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = width;
            canvas.height = height;
            
            const svgString = new XMLSerializer().serializeToString(svgElement);
            const img = new Image();
            const svg = new Blob([svgString], {{ type: 'image/svg+xml;charset=utf-8' }});
            const url = URL.createObjectURL(svg);
            
            img.onload = function() {{
                ctx.fillStyle = '#0a0a0f';
                ctx.fillRect(0, 0, width, height);
                ctx.drawImage(img, 0, 0);
                
                const link = document.createElement('a');
                link.download = '{document_title.replace(" ", "_")}_mindmap.png';
                link.href = canvas.toDataURL();
                link.click();
                
                URL.revokeObjectURL(url);
            }};
            
            img.src = url;
        }}
        
        // Initialize everything
        initMindMap();
        
        // Set initial state
        setTimeout(() => {{
            updateNodeVisibility();
            updateNodeStyles();
            switchViewMode('radial');
            fitToScreen();
        }}, 1000);
    </script>
</body>
</html>"""
    
    return html




def save_mindmap_html(
    mindmap_data: Dict[str, Any],
    output_path: str,
    document_title: str = "Mappa Concettuale",
    metadata: Optional[Dict[str, str]] = None
) -> str:
    """
    Save mind map as HTML file.
    
    Args:
        mindmap_data: Dictionary with mind map structure
        output_path: Path where to save the HTML file
        document_title: Title of the document
        metadata: Optional metadata
        
    Returns:
        Path to the saved file
    """
    html = generate_mindmap_html(mindmap_data, document_title, metadata)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return str(output_file)
