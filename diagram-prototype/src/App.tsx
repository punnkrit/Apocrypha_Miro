import { useCallback, useState, useEffect, useRef } from 'react';
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
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Moon, Sun, ArrowRight, ArrowLeft, ArrowLeftRight, Minus, Type } from 'lucide-react';
import { Streamlit, RenderData } from 'streamlit-component-lib';
import EditableNode from './EditableNode';

const nodeTypes = {
  editableNode: EditableNode,
};

// Initial dummy nodes - will be replaced by Streamlit data
const initialNodes: Node[] = [];

let id = 1;
const getId = () => `node_${++id}_${Date.now()}`;

const Flow = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { getNodes, getEdges, screenToFlowPosition } = useReactFlow();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [theme, setTheme] = useState<'dark' | 'light'>('light'); 
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [selectedNodes, setSelectedNodes] = useState<Node[]>([]);

  // History for Undo/Redo
  const [history, setHistory] = useState<Array<{nodes: Node[], edges: Edge[]}>>([]);
  const [future, setFuture] = useState<Array<{nodes: Node[], edges: Edge[]}>>([]);
  
  // Clipboard for Copy/Paste
  const clipboardRef = useRef<Node[]>([]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Snapshot Helper
  const takeSnapshot = useCallback(() => {
      setHistory(h => [...h, { nodes: getNodes(), edges: getEdges() }]);
      setFuture([]);
  }, [getNodes, getEdges]);

  // Undo/Redo Logic
  const undo = useCallback(() => {
      if (history.length === 0) return;
      const previous = history[history.length - 1];
      const newHistory = history.slice(0, history.length - 1);
      
      setFuture(f => [{ nodes: getNodes(), edges: getEdges() }, ...f]);
      setHistory(newHistory);
      setNodes(previous.nodes);
      setEdges(previous.edges);
  }, [history, getNodes, getEdges, setNodes, setEdges]);

  const redo = useCallback(() => {
      if (future.length === 0) return;
      const next = future[0];
      const newFuture = future.slice(1);
      
      setHistory(h => [...h, { nodes: getNodes(), edges: getEdges() }]);
      setFuture(newFuture);
      setNodes(next.nodes);
      setEdges(next.edges);
  }, [future, getNodes, getEdges, setNodes, setEdges]);

  // Streamlit integration
  useEffect(() => {
    const onRender = (event: Event) => {
      const customEvent = event as CustomEvent<RenderData>;
      const args = customEvent.detail.args;
      
      if (args.nodes && Array.isArray(args.nodes)) {
         const highlights = args.highlight_nodes || [];
         
         setNodes((currentNodes) => {
             const newNodes = args.nodes.map((serverNode: any) => {
                 const existing = currentNodes.find(n => n.id === serverNode.id);
                 
                 const isHighlighted = highlights.includes(serverNode.id);
                 let style = { ...serverNode.style };
                 if (isHighlighted) {
                     // Pass highlight style to propStyle
                     // We don't set border here directly if we want EditableNode to handle it, 
                     // but we can pass it in style object which EditableNode merges.
                     style.border = '3px solid #ff9900';
                     style.boxShadow = '0 0 15px rgba(255, 153, 0, 0.6)';
                 }
                 
                 // Move visual styles to data.style to avoid double borders (React Flow wrapper vs Inner Div)
                 const visualStyle = { ...style };
                 // Keep only layout props in the main style passed to React Flow
                 const layoutStyle = { 
                    width: style.width, 
                    height: style.height, 
                    zIndex: style.zIndex,
                    // Ensure wrapper is transparent so we don't see double boxes
                    background: 'transparent',
                    border: 'none',
                    boxShadow: 'none'
                 };

                 return {
                     ...serverNode,
                     type: 'editableNode', // Force editableNode
                     position: existing ? existing.position : serverNode.position,
                     style: layoutStyle, 
                     data: { ...serverNode.data, style: visualStyle } // Pass visuals to data
                 };
             });
             
             if (currentNodes.length === 0) return newNodes;
             return newNodes;
         });
      }
      
      if (args.edges && Array.isArray(args.edges)) {
          setEdges(args.edges);
      }

      Streamlit.setFrameHeight(800);
    };

    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    Streamlit.setComponentReady();
    Streamlit.setFrameHeight(800);
    
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender);
    };
  }, [setNodes, setEdges]);

  // Wrappers to capture history
  const onConnectWrapper = useCallback((params: Connection) => {
        takeSnapshot(); // Snapshot before connecting
        const newEdge: Edge = { ...params, id: `e${params.source}-${params.target}`, type: 'smoothstep' };
        setEdges((eds) => addEdge(newEdge, eds));
    }, [setEdges, takeSnapshot]);

  const onNodeDragStart = useCallback(() => {
      takeSnapshot(); // Snapshot before drag starts
  }, [takeSnapshot]);

  const addNode = useCallback(() => {
    takeSnapshot();
    
    let position = { x: 300, y: 300 };
    
    if (reactFlowWrapper.current) {
        const { top, left, width, height } = reactFlowWrapper.current.getBoundingClientRect();
        const center = {
            x: left + width / 2,
            y: top + height / 2,
        };
        position = screenToFlowPosition(center);
        // Center the node (width 120, height 60)
        position.x -= 60;
        position.y -= 30;
    }

    const newNode: Node = {
      id: getId(),
      type: 'editableNode',
      position,
      data: { 
          label: 'New Node', 
          style: { 
              background: 'white', 
              border: '1px solid #777', 
              borderRadius: '5px',
              textAlign: 'center',
              fontSize: '16px',
              width: 150,
              height: 70
          } 
      },
      // Layout style for React Flow wrapper
      style: { 
          width: 150, 
          height: 70, 
          background: 'transparent', 
          border: 'none' 
      }
    };
    
    setNodes((nds) => nds.concat(newNode));
  }, [setNodes, takeSnapshot, screenToFlowPosition]);

  // Keyboard shortcuts
  useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
          // Undo: Ctrl+Z or Cmd+Z
          if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
              e.preventDefault();
              if (e.shiftKey) {
                  redo();
              } else {
                  undo();
              }
          }
          // Copy: Ctrl+C
          if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
              const selected = getNodes().filter(n => n.selected);
              if (selected.length > 0) {
                  clipboardRef.current = selected;
                  // console.log('Copied', selected.length);
              }
          }
          // Paste: Ctrl+V
          if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
              if (clipboardRef.current.length > 0) {
                  takeSnapshot();
                  const newNodes = clipboardRef.current.map(n => ({
                      ...n,
                      id: getId(),
                      position: { x: n.position.x + 50, y: n.position.y + 50 },
                      selected: true,
                      data: { ...n.data } // Clone data
                  }));
                  
                  // Deselect current
                  setNodes(nds => nds.map(n => ({ ...n, selected: false })).concat(newNodes));
              }
          }
      };
      
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo, getNodes, setNodes, takeSnapshot]);


  const onSelectionChange = useCallback(({ nodes, edges }: OnSelectionChangeParams) => {
    setSelectedNodes(nodes);
    if (edges.length === 1) {
      setSelectedEdge(edges[0]);
    } else {
      setSelectedEdge(null);
    }
  }, []);

  const updateEdgeMarker = (markerStart: boolean, markerEnd: boolean) => {
    if (!selectedEdge) return;
    takeSnapshot();
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
      
      Streamlit.setComponentValue({
          _contextUpdate: contextUpdate,
      });
  };

  const updateNodeFontSize = (delta: number) => {
      if (selectedNodes.length === 0) return;
      takeSnapshot();
      
      setNodes((nds) =>
          nds.map((n) => {
              if (selectedNodes.some(sn => sn.id === n.id)) {
                  const currentStyle = (n.data.style as React.CSSProperties) || {};
                  const currentSize = parseInt(String(currentStyle.fontSize || '16').replace('px', ''));
                  const newSize = Math.max(10, Math.min(48, currentSize + delta)); // Clamp between 10-48px
                  return {
                      ...n,
                      data: {
                          ...n.data,
                          style: {
                              ...currentStyle,
                              fontSize: `${newSize}px`
                          }
                      }
                  };
              }
              return n;
          })
      );
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div className="dndflow" style={{ display: 'flex', height: '800px', width: '100%' }}>
      <div className="reactflow-wrapper" ref={reactFlowWrapper} style={{ flexGrow: 1, height: '100%', width: '100%' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnectWrapper}
          onNodeDragStart={onNodeDragStart}
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
          {/* Task 8: Pronounced Grid */}
          <Background 
            gap={20} 
            size={2} 
            color={theme === 'dark' ? '#555' : '#888'} 
            variant={BackgroundVariant.Dots}
          />
          
          <Panel position="top-right" style={{ display: 'flex', gap: '10px', flexDirection: 'column', alignItems: 'flex-end' }}>
            <div style={{ background: 'var(--panel-bg)', padding: '8px', borderRadius: '5px', boxShadow: '0 0 5px var(--panel-shadow)', display: 'flex', gap: '10px', alignItems: 'center', color: 'var(--panel-text)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', userSelect: 'none' }}>
                    <input type="checkbox" checked={snapToGrid} onChange={e => setSnapToGrid(e.target.checked)} />
                    Snap to Grid
                </label>
                
                {selectedNodes.length > 0 && (
                    <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', borderLeft: '1px solid #ccc', paddingLeft: '10px' }}>
                            <Type size={16} />
                            <button 
                                onClick={() => updateNodeFontSize(-2)}
                                style={{ 
                                    padding: '2px 8px', 
                                    cursor: 'pointer', 
                                    background: 'var(--button-bg)', 
                                    color: 'var(--button-text)', 
                                    border: '1px solid #ccc', 
                                    borderRadius: '4px',
                                    fontWeight: 'bold',
                                    fontSize: '14px'
                                }}
                                title="Decrease font size"
                            >
                                A-
                            </button>
                            <button 
                                onClick={() => updateNodeFontSize(2)}
                                style={{ 
                                    padding: '2px 8px', 
                                    cursor: 'pointer', 
                                    background: 'var(--button-bg)', 
                                    color: 'var(--button-text)', 
                                    border: '1px solid #ccc', 
                                    borderRadius: '4px',
                                    fontWeight: 'bold',
                                    fontSize: '14px'
                                }}
                                title="Increase font size"
                            >
                                A+
                            </button>
                        </div>
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
                    </>
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
