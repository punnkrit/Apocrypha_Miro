import React, { useEffect, useRef, useState } from 'react'
import { Streamlit, RenderData } from 'streamlit-component-lib'
import { Board } from './Board'
import { BoardState } from './types'

const defaultBoard: BoardState = { nodes: [], edges: [], selection: [] }

export const App: React.FC = () => {
  const [renderData, setRenderData] = useState<RenderData | null>(null)
  const [board, setBoard] = useState<BoardState>(defaultBoard)
  const [connectMode, setConnectMode] = useState(false)
  const seededRef = useRef(false)

  useEffect(() => {
    function onRender(event: CustomEvent<RenderData>) {
      setRenderData(event.detail)
      const incoming = (event.detail.args as any)?.board as BoardState | undefined
      const hasIncoming = !!incoming && ((incoming.nodes && incoming.nodes.length > 0) || (incoming.edges && incoming.edges.length > 0))
      if (hasIncoming) {
        setBoard(incoming as BoardState)
      } else if (!seededRef.current) {
        const seed = qsrSeed()
        seededRef.current = true
        setBoard(seed)
        Streamlit.setComponentValue(seed)
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

  const qsrSeed = (): BoardState => {
    const nodes = [
      { id: 'franchise', x: 500, y: 80, label: 'Franchise', icon: '🏪' },
      { id: 'west', x: 250, y: 220, label: 'West_Group' },
      { id: 'central', x: 500, y: 220, label: 'Central_Group' },
      { id: 'east', x: 750, y: 220, label: 'East_Group' },
      // West: A E L P
      { id: 'west_A', x: 140, y: 330, label: 'Accounting' },
      { id: 'west_E', x: 210, y: 420, label: 'Expenses' },
      { id: 'west_L', x: 280, y: 330, label: 'Legal' },
      { id: 'west_P', x: 350, y: 420, label: 'Permits' },
      // Central: A E L P
      { id: 'central_A', x: 400, y: 330, label: 'Accounting' },
      { id: 'central_E', x: 470, y: 420, label: 'Expenses' },
      { id: 'central_L', x: 540, y: 330, label: 'Legal' },
      { id: 'central_P', x: 610, y: 420, label: 'Permits' },
      // East: A E L P
      { id: 'east_A', x: 660, y: 330, label: 'Accounting' },
      { id: 'east_E', x: 730, y: 420, label: 'Expenses' },
      { id: 'east_L', x: 800, y: 330, label: 'Legal' },
      { id: 'east_P', x: 870, y: 420, label: 'Permits' },
    ]
    const edges = [
      { id: 'e_f_w', from: 'franchise', to: 'west' },
      { id: 'e_f_c', from: 'franchise', to: 'central' },
      { id: 'e_f_e', from: 'franchise', to: 'east' },
      // West children
      { id: 'e_w_A', from: 'west', to: 'west_A' },
      { id: 'e_w_E', from: 'west', to: 'west_E' },
      { id: 'e_w_L', from: 'west', to: 'west_L' },
      { id: 'e_w_P', from: 'west', to: 'west_P' },
      // Central children
      { id: 'e_c_A', from: 'central', to: 'central_A' },
      { id: 'e_c_E', from: 'central', to: 'central_E' },
      { id: 'e_c_L', from: 'central', to: 'central_L' },
      { id: 'e_c_P', from: 'central', to: 'central_P' },
      // East children
      { id: 'e_e_A', from: 'east', to: 'east_A' },
      { id: 'e_e_E', from: 'east', to: 'east_E' },
      { id: 'e_e_L', from: 'east', to: 'east_L' },
      { id: 'e_e_P', from: 'east', to: 'east_P' },
    ]
    return { nodes, edges, selection: [] }
  }

  const ensureSeed = () => {
    if (board.nodes.length === 0) {
      commitBoard(qsrSeed())
    }
  }

  useEffect(ensureSeed, [])

  return (
    <div style={{ height: 700, display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: 8, borderBottom: '1px solid #eee', display: 'flex', gap: 8 }}>
        <button onClick={() => commitBoard(defaultBoard)}>Reset</button>
        <button onClick={() => commitBoard(qsrSeed())}>Seed</button>
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
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <Board
          board={board}
          onChange={setBoard}
          onCommit={commitBoard}
          connectMode={connectMode}
        />
      </div>
    </div>
  )
}


