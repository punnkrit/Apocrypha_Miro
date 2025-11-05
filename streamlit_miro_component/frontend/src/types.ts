export type NodeId = string;

export interface BoardNode {
  id: NodeId;
  x: number;
  y: number;
  label: string;
  icon?: string; // emoji or short text
}

export interface BoardEdge {
  id: string;
  from: NodeId;
  to: NodeId;
}

export interface BoardState {
  nodes: BoardNode[];
  edges: BoardEdge[];
  selection: NodeId[];
}

