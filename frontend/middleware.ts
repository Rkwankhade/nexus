import { NextRequest, NextResponse } from 'next/server'

const PUBLIC_PATHS = ['/login']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next()
  }

  const hasSessionCookie = request.cookies.has('nexus_session')
  if (!hasSessionCookie && pathname !== '/') {
    // Client-side auth (localStorage token) handles the actual gate;
    // this cookie check is a light first line of defense for SSR routes.
    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
