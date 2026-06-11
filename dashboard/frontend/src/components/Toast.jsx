import { useState, useEffect, useCallback, createContext, useContext } from 'react'

const ToastContext = createContext()

export function useToast() {
  return useContext(ToastContext)
}

let toastId = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'info', duration = 3000) => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, duration)
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const colors = {
    info: { bg: '#00e5ff11', border: '#00e5ff44', text: '#00e5ff' },
    success: { bg: '#00ff8811', border: '#00ff8844', text: '#00ff88' },
    warning: { bg: '#ffaa0011', border: '#ffaa0044', text: '#ffaa00' },
    error: { bg: '#ff334411', border: '#ff334444', text: '#ff3344' },
  }

  return (
    <ToastContext.Provider value={addToast}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => {
          const c = colors[t.type] || colors.info
          return (
            <div
              key={t.id}
              onClick={() => removeToast(t.id)}
              className="pointer-events-auto px-3 py-2 text-xs font-mono border cursor-pointer animate-slide-in"
              style={{
                background: c.bg,
                borderColor: c.border,
                color: c.text,
                minWidth: 200,
                backdropFilter: 'blur(8px)',
              }}
            >
              {t.message}
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
