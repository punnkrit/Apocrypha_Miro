import React, { useEffect, useState } from 'react'
import { Streamlit, RenderData } from 'streamlit-component-lib'
import { Board } from './Board'
import { BoardState } from './types'

const defaultBoard: BoardState = { nodes: [], edges: [], selection: [] }

export const App: React.FC = () => {
  const [renderData, setRenderData] = useState<RenderData | null>(null)
  const [board, setBoard] = useState<BoardState>(defaultBoard)
  const [connectMode, setConnectMode] = useState(false)
  const [dragMode, setDragMode] = useState(false)

  useEffect(() => {
    function onRender(event: CustomEvent<RenderData>) {
      setRenderData(event.detail)
      const incoming = (event.detail.args as any)?.board as BoardState | undefined
      if (incoming) {
        setBoard(incoming)
      }
      Streamlit.setFrameHeight()
    }
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender as any)
    Streamlit.setComponentReady()
    Streamlit.setFrameHeight()
    return () => {
      Streamlit.events.removeEventListener(Streamlit.RENDER_EVENT, onRender as any)
    }
  }, [])

  // Only call setComponentValue on discrete commit events to avoid flicker.
  const commitBoard = (next: BoardState) => {
    setBoard(next)
    Streamlit.setComponentValue(next)
  }

  const handleAddToContext = () => {
    if (board.selection.length === 0) return
    const selectedNodes = board.nodes.filter((n) => board.selection.includes(n.id))
    const contextUpdate = {
      type: 'add_to_context',
      nodes: selectedNodes.map((n) => ({ id: n.id, label: n.label })),
    }
    Streamlit.setComponentValue({ ...board, _contextUpdate: contextUpdate })
  }

  const hasSelection = board.selection.length > 0

  return (
    <div style={{ height: 700, display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: 8, borderBottom: '1px solid #eee', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <button onClick={() => commitBoard(defaultBoard)}>Reset</button>
        <button
          onClick={() => {
            const id = `n_${Date.now()}`
            const next = {
              ...board,
              nodes: [...board.nodes, { id, x: 200, y: 200, label: 'Node', icon: '🔷' }],
              selection: [id],
            }
            commitBoard(next)
          }}
        >
          Add Node
        </button>
        <button
          onClick={() => {
            const toDelete = new Set(board.selection)
            if (toDelete.size === 0) return
            const nodes = board.nodes.filter((n) => !toDelete.has(n.id))
            const edges = board.edges.filter((e) => !toDelete.has(e.from) && !toDelete.has(e.to))
            commitBoard({ ...board, nodes, edges, selection: [] })
          }}
        >
          Delete Selected
        </button>
        <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <input type="checkbox" checked={connectMode} onChange={(e) => setConnectMode(e.target.checked)} />
          Connect Mode
        </label>
        <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <input type="checkbox" checked={dragMode} onChange={(e) => setDragMode(e.target.checked)} />
          Drag Mode
        </label>
        {hasSelection && (
          <button
            onClick={handleAddToContext}
            style={{
              backgroundColor: '#4a90e2',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            Add to Context
          </button>
        )}
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <Board
          board={board}
          onChange={setBoard}
          onCommit={commitBoard}
          connectMode={connectMode}
          dragMode={dragMode}
        />
      </div>
    </div>
  )
}


