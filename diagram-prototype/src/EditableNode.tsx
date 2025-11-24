import { Handle, Position, NodeProps, NodeResizer, useReactFlow } from '@xyflow/react';
import { useState, useRef, useEffect } from 'react';

export default function EditableNode({ id, data, selected, width, height }: NodeProps) {
  const { setNodes } = useReactFlow();
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label as string);
  const inputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setLabel(data.label as string);
  }, [data.label]);

  useEffect(() => {
    if (isEditing) {
       if (textareaRef.current) {
         textareaRef.current.focus();
         textareaRef.current.select();
       } else if (inputRef.current) {
         inputRef.current.focus();
         inputRef.current.select();
       }
    }
  }, [isEditing]);

  const updateLabel = () => {
      setNodes((nds) => nds.map((n) => {
          if (n.id === id) {
              return { ...n, data: { ...n.data, label } };
          }
          return n;
      }));
  };

  const onDoubleClick = () => {
    setIsEditing(true);
  };

  const onBlur = () => {
    setIsEditing(false);
    updateLabel();
  };

  const onKeyDown = (evt: React.KeyboardEvent) => {
    if (evt.key === 'Enter' && !evt.shiftKey) {
        evt.preventDefault(); 
        setIsEditing(false);
        updateLabel();
    }
  };

  const onChange = (evt: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setLabel(evt.target.value);
  };
  
// Task 3, 11: Pronounced outlines and Blue Highlight
  // We prioritize propStyle (search highlights) over default styles, but selection style over normal border
  
  // Recover the style from data.style (visuals) and propStyle (layout/overrides)
  // Note: propStyle now mainly contains layout info (width/height) and transparent bg/border from App.tsx
  const visualStyle = (data.style as React.CSSProperties) || {};
  
  const style: React.CSSProperties = {
    ...visualStyle, // Include styles from parent (e.g. search highlight, border, color)
    padding: '10px',
    borderRadius: '5px',
    background: visualStyle.background || 'var(--node-bg, white)',
    // Task 3: Pronounced outline. If highlighted by search (orange), keep it. If selected (blue), override.
    border: selected ? '2px solid #2684FF' : (visualStyle.border || '2px solid #333'), 
    textAlign: 'center',
    color: 'var(--node-color, black)',
    // Task 11: Blue Highlight. If selected, blue shadow. If search highlighted, orange shadow.
    boxShadow: selected ? '0 0 0 4px rgba(38, 132, 255, 0.3)' : (visualStyle.boxShadow || 'none'),
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    // Use width/height from props (which come from node.style in React Flow)
    // If not present, fallback to visualStyle or defaults
    width: width ? `${width}px` : (visualStyle.width ? `${visualStyle.width}px` : 'auto'),
    height: height ? `${height}px` : (visualStyle.height ? `${visualStyle.height}px` : 'auto'),
    minWidth: '100px',
    minHeight: '40px',
    boxSizing: 'border-box',
  };

  // Task 2: Connection points visible only when selected (node clicked state)
  const handleStyle = {
    background: '#555',
    width: 8,
    height: 8,
    opacity: selected ? 1 : 0,
    transition: 'opacity 0.2s',
    zIndex: 10,
  };
  
  // Task 4: NodeResizer allows resizing freely when selected
  return (
    <>
      <NodeResizer 
        minWidth={100} 
        minHeight={40} 
        isVisible={selected} 
        lineStyle={{border: '1px solid #2684FF'}} 
        handleStyle={{width: 8, height: 8, borderRadius: 2, background: '#2684FF'}} 
      />
      
      <div 
        onDoubleClick={onDoubleClick}
        style={style}
      >
        {/* Task 6, 7: 4 Connection points, connect from anywhere to anywhere */}
        {/* We place both Source and Target handles at each position */}
        
        {/* Top */}
        <Handle type="target" position={Position.Top} id="top-target" style={{ ...handleStyle, top: -4 }} />
        <Handle type="source" position={Position.Top} id="top-source" style={{ ...handleStyle, top: -4 }} />
        
        {/* Left */}
        <Handle type="target" position={Position.Left} id="left-target" style={{ ...handleStyle, left: -4 }} />
        <Handle type="source" position={Position.Left} id="left-source" style={{ ...handleStyle, left: -4 }} />
        
        {isEditing ? (
            <textarea
            ref={textareaRef}
            value={label}
            onChange={onChange}
            onBlur={onBlur}
            onKeyDown={onKeyDown}
            className="nodrag" 
            style={{
                width: '100%',
                height: '100%',
                border: 'none',
                outline: 'none',
                textAlign: 'center',
                background: 'transparent',
                fontFamily: 'inherit',
                fontSize: 'inherit',
                color: 'inherit',
                resize: 'none', 
                overflow: 'hidden',
            }}
            />
        ) : (
            <div style={{ 
                width: '100%', 
                wordBreak: 'break-word', 
                pointerEvents: 'none', 
                userSelect: 'none' 
            }}>
                {label}
            </div>
        )}

        {/* Right */}
        <Handle type="source" position={Position.Right} id="right-source" style={{ ...handleStyle, right: -4 }} />
        <Handle type="target" position={Position.Right} id="right-target" style={{ ...handleStyle, right: -4 }} />

        {/* Bottom */}
        <Handle type="source" position={Position.Bottom} id="bottom-source" style={{ ...handleStyle, bottom: -4 }} />
        <Handle type="target" position={Position.Bottom} id="bottom-target" style={{ ...handleStyle, bottom: -4 }} />
      </div>
    </>
  );
}
