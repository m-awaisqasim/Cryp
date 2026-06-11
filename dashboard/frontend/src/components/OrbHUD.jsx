import { useEffect, useRef } from 'react'

const RING_COUNT = 12
const ARC_RINGS = [
  { frac: 0.50, width: 3.5, arc: 120, gap: 75 },
  { frac: 0.42, width: 2.5, arc: 82,  gap: 53 },
  { frac: 0.34, width: 1.5, arc: 60,  gap: 38 },
]
const CIRCLE_BARS = 36
const HEX_CHARS = ['0x', 'A1', '7F', 'E4', '1B', 'FF', '3C', 'D9', '8A', '52']

const COLORS = {
  bg: '#00060a', pri: '#00d4ff', priLight: '#66e8ff',
  priDim: '#007a99', priGho: '#001f2e', acc: '#ff6b00',
  acc2: '#ffcc00', green: '#00ff88', red: '#ff3355',
  muted: '#ff3366', text: '#8ffcff', textDim: '#3a8a9a',
}

function hex(c, a) {
  return c + Math.max(0, Math.min(255, Math.round(a))).toString(16).padStart(2, '0')
}

export default function OrbHUD({ state = 'idle', muted = false, speaking = false }) {
  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const stateRef = useRef(state)
  const mutedRef = useRef(muted)
  const speakingRef = useRef(speaking)

  useEffect(() => { stateRef.current = state }, [state])
  useEffect(() => { mutedRef.current = muted }, [muted])
  useEffect(() => { speakingRef.current = speaking }, [speaking])

  useEffect(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    const ctx = canvas.getContext('2d')

    let W, H, cx, cy, fw
    let tick = 0
    let halo = 55
    let tgtHalo = 55
    let scale = 1
    let tgtScale = 1
    let lastTime = 0
    let scan = 0
    let scan2 = 180
    const rings = [0, 120, 240]
    const pulses = []
    const particles = []
    const dataBits = []
    const sparkles = []
    let glowPulse = 0
    let bgOffset = 0
    let beatFlash = 1
    let blink = true
    let blinkTick = 0
    let sleepT = 0
    let targetSleep = false
    let haloUpdateTimer = 0

    function resize() {
      const rect = container.getBoundingClientRect()
      W = rect.width
      H = rect.height
      cx = W / 2
      cy = H / 2
      fw = Math.min(W, H)
      const dpr = window.devicePixelRatio || 1
      canvas.width = W * dpr
      canvas.height = H * dpr
      ctx.scale(dpr, dpr)
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(container)

    function render(now) {
      tick++
      const s = stateRef.current
      const m = mutedRef.current
      const spk = speakingRef.current

      const sf = 1 - sleepT

      if (!lastTime) lastTime = now
      const dt = (now - lastTime) / 1000
      lastTime = now

      if (targetSleep && sleepT < 1) sleepT = Math.min(1, sleepT + 1 / 60)
      else if (!targetSleep && sleepT > 0) sleepT = Math.max(0, sleepT - 1 / 60)

      // halo & scale target updates
      haloUpdateTimer += dt
      if (haloUpdateTimer > (spk ? 0.12 : 0.5)) {
        haloUpdateTimer = 0
        if (spk) {
          tgtScale = 1.06 + Math.random() * 0.08
          tgtHalo = 155 + Math.random() * 45
        } else if (m) {
          tgtScale = 0.998 + Math.random() * 0.004
          tgtHalo = 15 + Math.random() * 13
        } else {
          const sineMod = 1 + 0.06 * Math.sin(tick * 0.025)
          tgtScale = 1.002 * sineMod
          tgtHalo = (50 + Math.random() * 22) * sineMod
        }
        if (sleepT > 0) tgtHalo *= (1 - sleepT * 0.7)
      }

      const sp = spk ? 0.38 : 0.15
      scale += (tgtScale - scale) * sp
      halo += (tgtHalo - halo) * sp

      // rings
      const ringSpeeds = spk ? [1.5, -1.1, 2.2] : [0.55, -0.35, 0.9]
      for (let i = 0; i < 3; i++) {
        rings[i] = (rings[i] + ringSpeeds[i] * (0.05 + 0.95 * sf)) % 360
      }

      // scanners
      scan = (scan + (spk ? 3.5 : 1.3) * (0.05 + 0.95 * sf)) % 360
      scan2 = (scan2 + (spk ? -2.4 : -0.75) * (0.05 + 0.95 * sf)) % 360

      // pulse rings
      const lim = fw * 0.74
      const pspd = (spk ? 4.8 : 2.0) * (0.05 + 0.95 * sf)
      for (let i = pulses.length - 1; i >= 0; i--) {
        pulses[i] += pspd
        if (pulses[i] >= lim) pulses.splice(i, 1)
      }
      if (pulses.length < 3 && Math.random() < (spk ? 0.09 : 0.025) * (0.05 + 0.95 * sf)) {
        pulses.push(0)
      }

      // glow pulse
      glowPulse = (glowPulse + (spk ? 0.04 : 0.015) * (0.05 + 0.95 * sf)) % (Math.PI * 2)

      // particles
      if (spk && Math.random() < 0.32 * (0.05 + 0.95 * sf)) {
        const ang = Math.random() * Math.PI * 2
        const rs = fw * 0.28
        particles.push({
          x: cx + Math.cos(ang) * rs,
          y: cy + Math.sin(ang) * rs,
          vx: Math.cos(ang) * (0.9 + Math.random() * 1.5),
          vy: Math.sin(ang) * (0.9 + Math.random() * 1.5) - 0.4,
          life: 1,
        })
      }
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]
        p.x += p.vx; p.y += p.vy
        p.vx *= 0.97; p.vy *= 0.97
        p.life -= 0.028
        if (p.life <= 0) particles.splice(i, 1)
      }

      // data bits
      if (Math.random() < (spk ? 0.04 : 0.015) * (0.05 + 0.95 * sf)) {
        const ang = Math.random() * Math.PI * 2
        const dist = fw * (0.3 + Math.random() * 0.25)
        dataBits.push({
          x: cx + Math.cos(ang) * dist, y: cy + Math.sin(ang) * dist,
          vx: Math.cos(ang) * (0.15 + Math.random() * 0.25),
          vy: Math.sin(ang) * (0.15 + Math.random() * 0.25) - 0.1,
          life: 1, text: HEX_CHARS[Math.floor(Math.random() * HEX_CHARS.length)],
        })
      }
      for (let i = dataBits.length - 1; i >= 0; i--) {
        const d = dataBits[i]
        d.x += d.vx; d.y += d.vy
        d.vx *= 0.99; d.vy = d.vy * 0.99 - 0.002
        d.life -= 0.006
        if (d.life <= 0) dataBits.splice(i, 1)
      }

      // sparkles
      if (Math.random() < (spk ? 0.08 : 0.03) * (0.05 + 0.95 * sf)) {
        sparkles.push({
          x: Math.random() * W, y: Math.random() * H,
          vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
          life: 1, size: 1.5 + Math.random() * 2,
        })
      }
      for (let i = sparkles.length - 1; i >= 0; i--) {
        const s = sparkles[i]
        s.x += s.vx; s.y += s.vy
        s.vx *= 0.98; s.vy *= 0.98
        s.life -= 0.018
        if (s.life <= 0) sparkles.splice(i, 1)
      }

      bgOffset = (bgOffset + 0.12 * (0.05 + 0.95 * sf)) % 48

      blinkTick++
      if (blinkTick >= 38) { blink = !blink; blinkTick = 0 }

      beatFlash = Math.max(0.5, beatFlash - 0.04)

      // --- DRAW ---
      const ringColor = m ? COLORS.muted : COLORS.pri
      const gpv = 0.85 + 0.15 * Math.sin(glowPulse)
      const bf = beatFlash

      ctx.clearRect(0, 0, W, H)

      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, fw * 0.7)
      grad.addColorStop(0, '#001824')
      grad.addColorStop(0.6, COLORS.bg)
      grad.addColorStop(1, COLORS.bg)
      ctx.fillStyle = grad
      ctx.fillRect(0, 0, W, H)

      // grid dots
      const gpAlpha = 80 + 40 * Math.sin(tick * 0.015)
      ctx.fillStyle = hex(COLORS.priGho, gpAlpha)
      for (let x = -bgOffset % 48; x < W; x += 48) {
        for (let y = -bgOffset % 48; y < H; y += 48) {
          const dx = Math.abs(x - cx), dy = Math.abs(y - cy)
          if (dx > fw * 0.55 || dy > fw * 0.55) {
            ctx.fillRect(x, y, 1, 1)
          }
        }
      }

      // halo rings (12 concentric)
      const faceR = fw * 0.31
      for (let i = 0; i < RING_COUNT; i++) {
        const r = faceR * (1.9 - i * 0.07)
        const a = Math.max(0, Math.min(255, Math.round(halo * 0.09 * (1 - i / RING_COUNT) * gpv)))
        ctx.strokeStyle = hex(ringColor, a)
        ctx.lineWidth = 1.8 - i * 0.1
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.stroke()
      }

      // pulse rings
      for (const pr of pulses) {
        const a = Math.max(0, Math.round(230 * (1 - pr / lim)))
        ctx.strokeStyle = hex(ringColor, a)
        ctx.lineWidth = 1.8
        ctx.beginPath()
        ctx.arc(cx, cy, pr, 0, Math.PI * 2)
        ctx.stroke()
      }

      // spinning arc rings
      for (let idx = 0; idx < ARC_RINGS.length; idx++) {
        const ar = ARC_RINGS[idx]
        const rr = fw * ar.frac
        const ba = rings[idx]
        const aVal = Math.max(0, Math.min(255, Math.round(halo * (1 - idx * 0.18) * gpv * bf)))
        ctx.strokeStyle = hex(ringColor, aVal)
        ctx.lineWidth = ar.width * bf
        let angle = ba
        while (angle < ba + 360) {
          const startRad = (angle * Math.PI) / 180
          const endRad = ((angle + ar.arc) * Math.PI) / 180
          ctx.beginPath()
          ctx.arc(cx, cy, rr, startRad, endRad)
          ctx.stroke()
          angle += ar.arc + ar.gap
        }
      }

      // scanner arcs
      const sr = fw * 0.52
      const sa = Math.max(0, Math.min(255, Math.round(halo * 1.6 * gpv)))
      const scanColor = m ? COLORS.muted : COLORS.pri
      for (let ti = 3; ti > 0; ti--) {
        const trailA = Math.floor(sa / (ti * 3))
        const trailW = 2.5 - ti * 0.4
        if (trailA > 5 && trailW > 0.5) {
          ctx.strokeStyle = hex(scanColor, trailA)
          ctx.lineWidth = trailW
          const sRad = ((scan - ti * 8) * Math.PI) / 180
          const eRad = ((scan - ti * 8 + 80) * Math.PI) / 180
          ctx.beginPath()
          ctx.arc(cx, cy, sr, sRad, eRad)
          ctx.stroke()
        }
      }
      ctx.strokeStyle = hex(scanColor, sa)
      ctx.lineWidth = 3
      const sRad1 = (scan * Math.PI) / 180
      const eRad1 = ((scan + 80) * Math.PI) / 180
      ctx.beginPath()
      ctx.arc(cx, cy, sr, sRad1, eRad1)
      ctx.stroke()
      ctx.strokeStyle = hex(COLORS.acc, Math.floor(sa / 2))
      ctx.lineWidth = 1.8
      const sRad2 = (scan2 * Math.PI) / 180
      const eRad2 = ((scan2 + 80) * Math.PI) / 180
      ctx.beginPath()
      ctx.arc(cx, cy, sr, sRad2, eRad2)
      ctx.stroke()

      // tick marks
      const tOut = fw * 0.508
      const tIn = fw * 0.483
      for (let deg = 0; deg < 360; deg += 5) {
        const rad = (deg * Math.PI) / 180
        let tickCol, tW, inn
        if (deg % 30 === 0) {
          tickCol = hex(m ? COLORS.muted : COLORS.priLight, 180)
          tW = 1.8; inn = tIn
        } else if (deg % 15 === 0) {
          tickCol = hex(m ? COLORS.muted : COLORS.pri, 120)
          tW = 1.3; inn = tIn + 4
        } else {
          tickCol = hex(m ? '#661933' : COLORS.priDim, 80)
          tW = 1; inn = tIn + 8
        }
        ctx.strokeStyle = tickCol
        ctx.lineWidth = tW
        ctx.beginPath()
        ctx.moveTo(cx + tOut * Math.cos(rad), cy - tOut * Math.sin(rad))
        ctx.lineTo(cx + inn * Math.cos(rad), cy - inn * Math.sin(rad))
        ctx.stroke()
      }

      // crosshair
      const chR = fw * 0.52
      const gapH = fw * 0.16
      const chA = Math.max(0, Math.min(255, Math.round(halo * 0.5 * gpv)))
      ctx.strokeStyle = hex(ringColor, chA)
      ctx.lineWidth = 1.2
      ctx.beginPath()
      ctx.moveTo(cx - chR, cy); ctx.lineTo(cx - gapH, cy)
      ctx.moveTo(cx + gapH, cy); ctx.lineTo(cx + chR, cy)
      ctx.moveTo(cx, cy - chR); ctx.lineTo(cx, cy - gapH)
      ctx.moveTo(cx, cy + gapH); ctx.lineTo(cx, cy + chR)
      ctx.stroke()

      // corner brackets
      const bl = 26
      const bc = hex(ringColor, 210)
      ctx.strokeStyle = bc
      ctx.lineWidth = 2.5
      const hl = cx - fw / 2, hr = cx + fw / 2
      const ht = cy - fw / 2, hb = cy + fw / 2
      const corners = [[hl, ht, 1, 1], [hr, ht, -1, 1], [hl, hb, 1, -1], [hr, hb, -1, -1]]
      for (const [bx, by, dx, dy] of corners) {
        ctx.beginPath()
        ctx.moveTo(bx, by); ctx.lineTo(bx + dx * bl, by)
        ctx.moveTo(bx, by); ctx.lineTo(bx, by + dy * bl)
        ctx.stroke()
      }

      // orb/face
      const orbR = fw * 0.27 * scale
      for (let i = 8; i > 0; i--) {
        const r2 = orbR * i / 8
        const frc = i / 8
        const a = Math.max(0, Math.min(255, Math.round(halo * 1.1 * frc)))
        const oc = m ? [200, 0, 50] : [0, 60, 110]
        ctx.fillStyle = `rgba(${oc[0] * frc},${oc[1] * frc},${oc[2] * frc},${a / 255})`
        ctx.beginPath()
        ctx.arc(cx, cy, r2, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.fillStyle = hex(COLORS.pri, Math.min(255, Math.round(halo * 2)))
      ctx.font = 'bold 14px "Courier New", monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText('J.A.R.V.I.S', cx, cy)

      // particles
      for (const p of particles) {
        const a = Math.max(0, Math.min(255, Math.round(p.life * 255)))
        ctx.fillStyle = hex(ringColor, a)
        ctx.beginPath()
        ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2)
        ctx.fill()
      }

      // data bits
      for (const d of dataBits) {
        const a = Math.max(0, Math.min(255, Math.round(d.life * 200)))
        ctx.fillStyle = hex(ringColor, a)
        ctx.font = 'bold 7px "Courier New", monospace'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(d.text, d.x, d.y)
      }

      // sparkles
      for (const s of sparkles) {
        const a = Math.max(0, Math.min(255, Math.round(s.life * 220)))
        ctx.fillStyle = hex(Math.random() > 0.5 ? '#d8f8ff' : ringColor, a)
        ctx.beginPath()
        ctx.arc(s.x, s.y, s.size * s.life, 0, Math.PI * 2)
        ctx.fill()
      }

      // status text
      let txt, col
      const sy = cy + fw * 0.42
      if (m) {
        txt = '\u2298  MUTED'
        col = COLORS.muted
      } else if (spk) {
        txt = '\u25CF  SPEAKING'
        col = COLORS.green
      } else if (s === 'THINKING') {
        txt = (blink ? '\u25C8' : '\u25C7') + '  THINKING'
        col = COLORS.acc2
      } else if (s === 'PROCESSING') {
        txt = (blink ? '\u25B7' : '\u25B6') + '  PROCESSING'
        col = COLORS.acc2
      } else if (s === 'LISTENING') {
        txt = (blink ? '\u25CF' : '\u25CB') + '  LISTENING'
        col = COLORS.green
      } else {
        txt = (blink ? '\u25CF' : '\u25CB') + '  ' + s
        col = COLORS.pri
      }
      ctx.fillStyle = col
      ctx.font = 'bold 11px "Courier New", monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(txt, cx, sy)

      // circular waveform
      const rInner = fw * 0.33
      const rOuter = fw * 0.47
      for (let i = 0; i < CIRCLE_BARS; i++) {
        const angleRad = (i * (360 / CIRCLE_BARS) - 90) * Math.PI / 180
        let mag
        if (spk) {
          mag = Math.min(1, 0.3 + 0.7 * Math.abs(Math.sin(tick * 0.05 + i * 0.3)))
        } else if (m) {
          mag = 0.01
        } else {
          mag = 0.04 + 0.02 * Math.sin(tick * 0.05 + i * 0.4)
        }
        const barLen = Math.max(2, mag * (rOuter - rInner))
        const rEnd = rInner + barLen
        const x1 = cx + rInner * Math.cos(angleRad)
        const y1 = cy + rInner * Math.sin(angleRad)
        const x2 = cx + rEnd * Math.cos(angleRad)
        const y2 = cy + rEnd * Math.sin(angleRad)
        let cl
        if (mag > 0.5) cl = hex(COLORS.acc, 200)
        else if (mag > 0.25) cl = hex(COLORS.pri, 180)
        else cl = hex(COLORS.priDim, 100)
        ctx.strokeStyle = cl
        ctx.lineWidth = 2.5
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.stroke()
      }

      animRef = requestAnimationFrame(render)
    }

    let animRef = requestAnimationFrame(render)
    return () => {
      cancelAnimationFrame(animRef)
      ro.disconnect()
    }
  }, [])

  return (
    <div ref={containerRef} className="w-full h-full min-h-0">
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  )
}
