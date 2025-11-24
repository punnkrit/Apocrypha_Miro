import React from 'react';
import { Square, Circle } from 'lucide-react';

export default function Sidebar() {
  const onDragStart = (event: React.DragEvent, nodeType: string, label: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('application/reactflow-label', label);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <aside style={{ padding: '15px', borderRight: '1px solid #eee', background: '#fcfcfc', width: '250px', display: 'flex', flexDirection: 'column', gap: '10px', color: '#333' }}>
      <div className="description" style={{ marginBottom: '10px', fontSize: '14px', color: '#555' }}>
        Drag nodes to the pane on the right.
      </div>
      
      <div 
        className="dndnode input" 
        onDragStart={(event) => onDragStart(event, 'input', 'Start Node')} 
        draggable 
        style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '8px', background: 'white', color: '#333' }}
      >
        <Circle size={16} />
        Input Node
      </div>

      <div 
        className="dndnode" 
        onDragStart={(event) => onDragStart(event, 'default', 'Process Node')} 
        draggable
        style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '8px', background: 'white', color: '#333' }}
      >
        <Square size={16} />
        Default Node
      </div>

      <div 
        className="dndnode output" 
        onDragStart={(event) => onDragStart(event, 'output', 'End Node')} 
        draggable
        style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '4px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '8px', background: 'white', color: '#333' }}
      >
        <Circle size={16} />
        Output Node
      </div>
      
    </aside>
  );
}

