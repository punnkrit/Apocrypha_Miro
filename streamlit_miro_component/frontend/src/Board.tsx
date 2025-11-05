import React, { useCallback, useMemo, useRef, useState } from 'react'
import { BoardNode, BoardState } from './types'

type Props = {
  board: BoardState
  onChange: (next: BoardState) => void
  onCommit?: (next: BoardState) => void
  connectMode?: boolean
}

type Point = { x: number; y: number }

function clampZoom(z: number) {
  return Math.min(2.5, Math.max(0.3, z))
}

export const Board: React.FC<Props> = ({ board, onChange, onCommit, connectMode = false }) => {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState<Point>({ x: 0, y: 0 })
  const [drag, setDrag] = useState<null | { id: string; offset: Point }>(null)
  const [isPanning, setIsPanning] = useState(false)
  const panStart = useRef<Point | null>(null)
  const [pendingSourceId, setPendingSourceId] = useState<string | null>(null)

  const worldToScreen = useCallback(
    (p: Point) => ({ x: p.x * zoom + pan.x, y: p.y * zoom + pan.y }),
    [zoom, pan]
  )
  const screenToWorld = useCallback(
    (p: Point) => ({ x: (p.x - pan.x) / zoom, y: (p.y - pan.y) / zoom }),
    [zoom, pan]
  )

  const onWheel: React.WheelEventHandler<HTMLDivElement> = (e) => {
    e.preventDefault()
    const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect()
    const mouse: Point = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    const world = screenToWorld(mouse)
    const nextZoom = clampZoom(zoom * (e.deltaY < 0 ? 1.1 : 0.9))
    const nextPan: Point = {
      x: mouse.x - world.x * nextZoom,
      y: mouse.y - world.y * nextZoom,
    }
    setZoom(nextZoom)
    setPan(nextPan)
  }

  const startPan = (e: React.MouseEvent) => {
    if ((e.buttons & 1) === 0) return
    setIsPanning(true)
    panStart.current = { x: e.clientX - pan.x, y: e.clientY - pan.y }
  }
  const movePan = (e: React.MouseEvent) => {
    if (!isPanning || !panStart.current) return
    setPan({ x: e.clientX - panStart.current.x, y: e.clientY - panStart.current.y })
  }
  const endPan = () => {
    setIsPanning(false)
    panStart.current = null
  }

  const onMouseDownNode = (e: React.MouseEvent, node: BoardNode) => {
    e.stopPropagation()
    const rect = (containerRef.current as HTMLDivElement).getBoundingClientRect()
    const mouse: Point = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    const world = screenToWorld(mouse)
    if (connectMode) {
      if (!pendingSourceId) {
        setPendingSourceId(node.id)
        onChange({ ...board, selection: [node.id] })
      } else if (pendingSourceId && pendingSourceId !== node.id) {
        const newEdgeId = `e_${pendingSourceId}_${node.id}_${Date.now()}`
        const next = { ...board, edges: [...board.edges, { id: newEdgeId, from: pendingSourceId, to: node.id }], selection: [node.id] }
        setPendingSourceId(null)
        if (onCommit) onCommit(next)
        else onChange(next)
      }
    } else {
      setDrag({ id: node.id, offset: { x: world.x - node.x, y: world.y - node.y } })
      if (e.shiftKey) {
        const already = board.selection.includes(node.id)
        const nextSel = already ? board.selection.filter((id) => id !== node.id) : [...board.selection, node.id]
        onChange({ ...board, selection: nextSel })
      } else {
        onChange({ ...board, selection: [node.id] })
      }
    }
  }

  const onMouseMove = (e: React.MouseEvent) => {
    if (!drag) return
    const rect = (containerRef.current as HTMLDivElement).getBoundingClientRect()
    const mouse: Point = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    const world = screenToWorld(mouse)
    const nextNodes = board.nodes.map((n) =>
      n.id === drag.id ? { ...n, x: world.x - drag.offset.x, y: world.y - drag.offset.y } : n
    )
    onChange({ ...board, nodes: nextNodes })
  }

  const onMouseUp = () => {
    if (drag) {
      // Commit final position once per drag
      if (onCommit) onCommit(board)
    }
    setDrag(null)
  }

  const nodeStyle = useMemo(
    () => ({
      position: 'absolute' as const,
      width: 120,
      height: 60,
      borderRadius: 8,
      border: '1px solid #d0d0d0',
      background: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      userSelect: 'none' as const,
      cursor: drag ? 'grabbing' : 'grab',
    }),
    [drag]
  )

  const clearSelection = () => {
    if (board.selection.length || pendingSourceId) {
      setPendingSourceId(null)
      const next = { ...board, selection: [] }
      if (onCommit) onCommit(next)
      else onChange(next)
    }
  }

  const nodeCenter = (n: BoardNode) => ({ x: n.x + 60, y: n.y + 30 })

  return (
    <div
      ref={containerRef}
      style={{
        height: '100%',
        width: '100%',
        background: '#fafafa',
        overflow: 'hidden',
        position: 'relative',
      }}
      onWheel={onWheel}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseDown={startPan}
      onMouseLeave={endPan}
      onMouseEnter={() => {}}
    >
      <div
        style={{
          position: 'absolute',
          left: pan.x,
          top: pan.y,
          transform: `scale(${zoom})`,
          transformOrigin: '0 0',
          width: '100%',
          height: '100%',
        }}
        onMouseMove={movePan}
        onMouseUp={endPan}
        onClick={clearSelection}
      >
        {/* Edges layer */}
        <svg width="100%" height="100%" style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}>
          {board.edges.map((e) => {
            const from = board.nodes.find((n) => n.id === e.from)
            const to = board.nodes.find((n) => n.id === e.to)
            if (!from || !to) return null
            const a = nodeCenter(from)
            const b = nodeCenter(to)
            return (
              <line key={e.id} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#9bb6e0" strokeWidth={2} markerEnd={"url(#arrow)"} />
            )
          })}
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#9bb6e0" />
            </marker>
          </defs>
        </svg>
        {board.nodes.map((node) => {
          const selected = board.selection.includes(node.id)
          return (
            <div
              key={node.id}
              onMouseDown={(e) => onMouseDownNode(e, node)}
              style={{
                ...nodeStyle,
                left: node.x,
                top: node.y,
                borderColor: selected ? '#4a90e2' : '#d0d0d0',
                boxShadow: selected ? '0 0 0 2px rgba(74,144,226,0.25)' : nodeStyle.boxShadow,
              }}
            >
              <div style={{ fontSize: 20, marginRight: 8 }}>{node.icon || '⬜️'}</div>
              <div style={{ fontSize: 14 }}>{node.label}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}


