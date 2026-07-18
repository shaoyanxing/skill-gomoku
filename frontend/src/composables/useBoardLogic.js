// 棋盘基础逻辑：五子判定 / 活三检测（前端提示用，后端为权威判定）
export const DIRECTIONS = [[1, 0], [0, 1], [1, 1], [1, -1]]

export function inBoard(x, y) {
  return x >= 0 && x < 15 && y >= 0 && y < 15
}

export function checkFive(board, x, y, color) {
  for (const [dx, dy] of DIRECTIONS) {
    let count = 1
    for (const sign of [1, -1]) {
      let nx = x + dx * sign
      let ny = y + dy * sign
      while (inBoard(nx, ny) && board[ny][nx] === color) {
        count += 1
        nx += dx * sign
        ny += dy * sign
      }
    }
    if (count >= 5) return true
  }
  return false
}

export function hasLiveThree(board, color) {
  for (let y = 0; y < 15; y++) {
    for (let x = 0; x < 15; x++) {
      if (board[y][x]) continue
      for (const [dx, dy] of DIRECTIONS) {
        let count = 1
        let open = 0
        for (const sign of [1, -1]) {
          let nx = x + dx * sign
          let ny = y + dy * sign
          while (inBoard(nx, ny) && board[ny][nx] === color) {
            count += 1
            nx += dx * sign
            ny += dy * sign
          }
          if (inBoard(nx, ny) && !board[ny][nx]) open += 1
        }
        if (count === 3 && open === 2) return true
      }
    }
  }
  return false
}

export function useBoardLogic() {
  return { DIRECTIONS, inBoard, checkFive, hasLiveThree }
}