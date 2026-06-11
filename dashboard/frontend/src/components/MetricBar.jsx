import { useRef, useEffect } from 'react'

export default function MetricBar({ label, value = 0, color = '#00d4ff', width = 132, height = 38 }) {
  const canvasRef = useRef(null)
  const displayRef = useRef(0)
  const animRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    canvas.width = width * dpr
    canvas.height = height * dpr
    ctx.scale(dpr, dpr)

    const textColors = ['#3a8a9a', '#5ab8cc', '#00d4ff', '#ffcc00', '#ff3355']
    const barColors = ['#00d4ff', '#00d4ff', '#00d4ff', '#ff6b00', '#ff3355']

    const draw = () => {
      const dv = displayRef.current
      const diff = value - dv
      displayRef.current += diff * 0.18
      if (Math.abs(diff) < 0.1) displayRef.current = value

      const displayVal = displayRef.current
      const idx = displayVal > 85 ? 4 : displayVal > 65 ? 3 : 0
      const barCol = barColors[idx]

      ctx.clearRect(0, 0, width, height)

      ctx.fillStyle = '#010f18'
      ctx.strokeStyle = '#0f4060'
      ctx.lineWidth = 1
      roundRect(ctx, 1, 1, width - 2, height - 2, 4)
      ctx.fill()
      ctx.stroke()

      const bx = 7
      const by = height - 10
      const bw = width - 14
      const bh = 5
      const fw = Math.max(0, (bw * displayVal) / 100)

      ctx.fillStyle = '#011520'
      roundRect(ctx, bx, by, bw, bh, 2)
      ctx.fill()

      if (fw > 2) {
        const grad = ctx.createLinearGradient(bx, by, bx + fw, by)
        grad.addColorStop(0, barCol)
        grad.addColorStop(1, barCol + 'cc')
        ctx.fillStyle = grad
        roundRect(ctx, bx, by, fw, bh, 2)
        ctx.fill()

        if (fw > 10 && displayVal > 10) {
          ctx.fillStyle = barCol + '88'
          ctx.beginPath()
          ctx.arc(bx + fw, by + bh / 2, bh * 0.7, 0, Math.PI * 2)
          ctx.fill()
        }
      }

      ctx.font = 'bold 7px "Courier New", monospace'
      ctx.fillStyle = '#3a8a9a'
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      ctx.fillText(label, 8, 9)

      ctx.font = 'bold 9px "Courier New", monospace'
      ctx.fillStyle = barCol
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillText(value.toFixed(0) + '%', width - 8, 9)

      animRef.current = requestAnimationFrame(draw)
    }

    animRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(animRef.current)
  }, [label, value, width, height, color])

  return (
    <canvas
      ref={canvasRef}
      className="block"
      style={{ width, height }}
    />
  )
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}
