import { Handle, Position, NodeProps, NodeResizer } from '@xyflow/react';
import { useState, useRef, useEffect } from 'react';

export default function EditableNode({ data, selected, width, height }: NodeProps) {
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

  const onDoubleClick = () => {
    setIsEditing(true);
  };

  const onBlur = () => {
    setIsEditing(false);
    data.label = label; 
  };

  const onKeyDown = (evt: React.KeyboardEvent) => {
    if (evt.key === 'Enter' && !evt.shiftKey) {
        evt.preventDefault(); 
        setIsEditing(false);
        data.label = label;
    }
  };

  const onChange = (evt: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setLabel(evt.target.value);
  };
  
  const style: React.CSSProperties = {
    padding: '10px',
    borderRadius: '5px',
    background: 'var(--node-bg)',
    border: selected ? '2px solid var(--node-border-selected)' : '1px solid var(--node-border)',
    textAlign: 'center',
    color: 'var(--node-color)',
    boxShadow: selected ? '0 0 0 2px var(--node-shadow-selected)' : 'none',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    width: width ? `${width}px` : 'auto',
    height: height ? `${height}px` : 'auto',
    minWidth: '100px',
    minHeight: '40px',
    boxSizing: 'border-box',
  };

  const handleStyle = {
    background: 'var(--handle-bg)',
    opacity: selected ? 1 : 0,
    transition: 'opacity 0.2s',
  };

  return (
    <>
      <NodeResizer 
        minWidth={100} 
        minHeight={40} 
        isVisible={selected} 
        lineStyle={{border: '1px solid var(--node-border-selected)'}} 
        handleStyle={{width: 8, height: 8, borderRadius: 2, background: 'var(--handle-bg)'}} 
      />
      
      <div 
        onDoubleClick={onDoubleClick}
        style={style}
      >
        <Handle type="target" position={Position.Top} id="top" style={{ ...handleStyle, top: -5 }} />
        <Handle type="target" position={Position.Left} id="left" style={{ ...handleStyle, left: -5 }} />
        
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

        <Handle type="source" position={Position.Right} id="right" style={{ ...handleStyle, right: -5 }} />
        <Handle type="source" position={Position.Bottom} id="bottom" style={{ ...handleStyle, bottom: -5 }} />
      </div>
    </>
  );
}
