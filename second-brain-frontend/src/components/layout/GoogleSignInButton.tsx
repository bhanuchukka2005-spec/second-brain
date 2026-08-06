import { useEffect, useRef } from 'react'

const GOOGLE_CLIENT_ID =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ||
  '195046896396-a620heggt6bibibvfgsm2jktpm20ln5g.apps.googleusercontent.com'

interface Props {
  onToken: (idToken: string) => void
  onError: (msg: string) => void
}

export function GoogleSignInButton({ onToken, onError }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const init = () => {
      if (!window.google || !containerRef.current) return

      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) => {
          if (response.credential) {
            onToken(response.credential)
          } else {
            onError('Google sign-in cancelled or failed.')
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      })

      window.google.accounts.id.renderButton(containerRef.current, {
        theme: 'filled_black',
        size: 'large',
        width: 360,
        text: 'continue_with',
        shape: 'rectangular',
      })
    }

    if (window.google) {
      init()
    } else {
      const interval = setInterval(() => {
        if (window.google) {
          clearInterval(interval)
          init()
        }
      }, 100)
      return () => clearInterval(interval)
    }
  }, [onToken, onError])

  return (
    <div className="flex justify-center">
      <div ref={containerRef} />
    </div>
  )
}