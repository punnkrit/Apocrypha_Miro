import { useCallback, useState, useEffect } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  useReactFlow,
  Connection,
  Node,
  Panel,
  Edge,
  MarkerType,
  OnSelectionChangeParams,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Moon, Sun, ArrowRight, ArrowLeft, ArrowLeftRight, Minus } from 'lucide-react';
import { Streamlit, RenderData } from 'streamlit-component-lib';
import EditableNode from './EditableNode';

const nodeTypes = {
  editableNode: EditableNode,
};

// Initial dummy nodes - will be replaced by Streamlit data
const initialNodes: Node[] = [];

let id = 1;
const getId = () => `node_${++id}`;

const Flow = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { getNodes } = useReactFlow();
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [theme, setTheme] = useState<'dark' | 'light'>('light'); // Default to light for this app
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [selectedNodes, setSelectedNodes] = useState<Node[]>([]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Streamlit integration
  useEffect(() => {
    const onRender = (event: Event) => {
      const customEvent = event as CustomEvent<RenderData>;
      const args = customEvent.detail.args;
      
      // Only update if we have nodes from Python
      if (args.nodes && Array.isArray(args.nodes)) {
         const highlights = args.highlight_nodes || [];
         
         setNodes((currentNodes) => {
             // Map server nodes to local nodes, preserving position if they exist
             const newNodes = args.nodes.map((serverNode: any) => {
                 const existing = currentNodes.find(n => n.id === serverNode.id);
                 
                 // Highlight styling
                 const isHighlighted = highlights.includes(serverNode.id);
                 let style = { ...serverNode.style };
                 if (isHighlighted) {
                     style.border = '3px solid #ff9900';
                     style.boxShadow = '0 0 15px rgba(255, 153, 0, 0.6)';
                 }
                 
                 // Ensure we use the 'editableNode' type if that's what we want, 
                 // or 'default' if coming from app.py. 
                 // app.py sends 'default' type nodes. 
                 // We can map them to 'editableNode' if we want editing features, 
                 // or just use 'default' (which React Flow provides).
                 // For this integration, let's use what Python sends, but ensure types match.
                 
                 return {
                     ...serverNode,
                     position: existing ? existing.position : serverNode.position,
                     style,
                     // Preserve data label if editing was supported (optional)
                     data: { ...serverNode.data }
                 };
             });
             
             // If currentNodes is empty, just return newNodes
             if (currentNodes.length === 0) return newNodes;
             
             // Basic check to see if we should update (avoid loops if nothing changed)
             // For MVP, we just update. The preserving of position handles the main jitter issue.
             return newNodes;
         });
      }
      
      if (args.edges && Array.isArray(args.edges)) {
          setEdges(args.edges);
      }

      // Force a fixed height for the frame to ensure visibility
      Streamlit.setFrameHeight(800);
    };

    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    Streamlit.setComponentReady();
    
    // Initial height set
    Streamlit.setFrameHeight(800);
    
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender);
    };
  }, [setNodes, setEdges]);


  const onConnect = useCallback(
    (params: Connection) => {
        const newEdge: Edge = { ...params, id: `e${params.source}-${params.target}`, type: 'smoothstep' };
        setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges],
  );

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const addNode = useCallback(() => {
    const existingNodes = getNodes();
    const lastNode = existingNodes[existingNodes.length - 1];
    
    let position = { x: 300, y: 300 };
    
    if (lastNode) {
        position = { x: lastNode.position.x + 50, y: lastNode.position.y + 50 };
    } else {
         position = { x: 250, y: 250 };
    }

    const newNode: Node = {
      id: getId(),
      type: 'default', // Use default for consistency with Python nodes
      position,
      data: { label: 'New Node' },
      style: { background: 'white', border: '1px solid #777', padding: '10px', borderRadius: '5px' }
    };
    
    setNodes((nds) => nds.concat(newNode));
  }, [getNodes, setNodes]);

  const onSelectionChange = useCallback(({ nodes, edges }: OnSelectionChangeParams) => {
    setSelectedNodes(nodes);
    if (edges.length === 1) {
      setSelectedEdge(edges[0]);
    } else {
      setSelectedEdge(null);
    }
    
    // Optional: Send selection back to Streamlit immediately
    // Streamlit.setComponentValue({
    //     nodes: getNodes(),
    //     selection: nodes.map(n => n.id)
    // });
  }, []);

  const updateEdgeMarker = (markerStart: boolean, markerEnd: boolean) => {
    if (!selectedEdge) return;

    setEdges((eds) =>
      eds.map((e) => {
        if (e.id === selectedEdge.id) {
          return {
            ...e,
            markerStart: markerStart ? { type: MarkerType.ArrowClosed } : undefined,
            markerEnd: markerEnd ? { type: MarkerType.ArrowClosed } : undefined,
          };
        }
        return e;
      })
    );
  };

  const handleAddToContext = () => {
      if (selectedNodes.length === 0) return;
      
      const contextUpdate = {
          type: 'add_to_context',
          nodes: selectedNodes.map(n => ({ id: n.id, label: n.data.label })),
      };
      
      // Send the update to Streamlit
      Streamlit.setComponentValue({
          _contextUpdate: contextUpdate,
          // We can also send current state if we want to persist it
          // nodes: nodes,
          // edges: edges
      });
  };

  return (
    <div className="dndflow" style={{ display: 'flex', height: '800px', width: '100%' }}>
      <div className="reactflow-wrapper" style={{ flexGrow: 1, height: '100%', width: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onSelectionChange={onSelectionChange}
          nodeTypes={nodeTypes}
          fitView
          snapToGrid={snapToGrid}
          snapGrid={[15, 15]}
          deleteKeyCode={['Backspace', 'Delete']}
          colorMode={theme}
          defaultEdgeOptions={{
            style: { strokeWidth: 2, stroke: 'var(--edge-color)' },
            type: 'smoothstep',
          }}
        >
          <Controls style={{ fill: 'currentColor' }} />
          <Background gap={15} size={1} color={theme === 'dark' ? '#555' : '#aaa'} />
          
          <Panel position="top-right" style={{ display: 'flex', gap: '10px', flexDirection: 'column', alignItems: 'flex-end' }}>
            <div style={{ background: 'var(--panel-bg)', padding: '8px', borderRadius: '5px', boxShadow: '0 0 5px var(--panel-shadow)', display: 'flex', gap: '10px', alignItems: 'center', color: 'var(--panel-text)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', userSelect: 'none' }}>
                    <input type="checkbox" checked={snapToGrid} onChange={e => setSnapToGrid(e.target.checked)} />
                    Snap to Grid
                </label>
                
                {selectedNodes.length > 0 && (
                    <button 
                        onClick={handleAddToContext}
                        style={{ 
                            padding: '5px 10px', 
                            cursor: 'pointer', 
                            background: '#4A90E2', 
                            color: 'white', 
                            border: 'none', 
                            borderRadius: '4px',
                            fontWeight: 'bold'
                        }}
                    >
                        Add to Context
                    </button>
                )}

                <button onClick={addNode} style={{ padding: '5px 10px', cursor: 'pointer', background: 'var(--button-bg)', color: 'var(--button-text)', border: 'none', borderRadius: '4px' }}>
                    Add Node
                </button>
                <button onClick={toggleTheme} style={{ background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', color: 'var(--panel-text)' }}>
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>
            </div>

            {selectedEdge && (
               <div style={{ background: 'var(--panel-bg)', padding: '8px', borderRadius: '5px', boxShadow: '0 0 5px var(--panel-shadow)', display: 'flex', gap: '10px', alignItems: 'center', color: 'var(--panel-text)' }}>
                  <span style={{ fontSize: '14px', fontWeight: 500 }}>Line Endings:</span>
                  <button onClick={() => updateEdgeMarker(false, false)} title="None" style={{ background: 'transparent', border: '1px solid #ccc', padding: '4px', borderRadius: '4px', cursor: 'pointer', display: 'flex' }}>
                    <Minus size={16} />
                  </button>
                  <button onClick={() => updateEdgeMarker(false, true)} title="Arrow End" style={{ background: 'transparent', border: '1px solid #ccc', padding: '4px', borderRadius: '4px', cursor: 'pointer', display: 'flex' }}>
                    <ArrowRight size={16} />
                  </button>
                  <button onClick={() => updateEdgeMarker(true, false)} title="Arrow Start" style={{ background: 'transparent', border: '1px solid #ccc', padding: '4px', borderRadius: '4px', cursor: 'pointer', display: 'flex' }}>
                    <ArrowLeft size={16} />
                  </button>
                  <button onClick={() => updateEdgeMarker(true, true)} title="Both Ends" style={{ background: 'transparent', border: '1px solid #ccc', padding: '4px', borderRadius: '4px', cursor: 'pointer', display: 'flex' }}>
                    <ArrowLeftRight size={16} />
                  </button>
               </div> 
            )}
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <ReactFlowProvider>
      <Flow />
    </ReactFlowProvider>
  );
}
