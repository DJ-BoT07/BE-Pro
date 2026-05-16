import { clerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const publicPaths = ["/", "/sign-in*", "/sign-up*", "/api/load-data"];

function isPublic(path) {
  return publicPaths.some((x) =>
    path.match(new RegExp(`^${x}$`.replace("*$", "($|/)")))
  );
}

export const config = {
  matcher: ["/((?!static|.*\\..*|_next|favicon.ico).*)", "/"],
  runtime: "edge", // Explicitly specify Edge Runtime
};

export default clerkMiddleware((request) => {
  // Safely extract pathname with fallback
  let pathname = "/";
  
  if (request.nextUrl) {
    pathname = request.nextUrl.pathname;
  } else if (request.url) {
    try {
      const url = new URL(request.url);
      pathname = url.pathname;
    } catch (e) {
      pathname = "/";
    }
  }

  if (isPublic(pathname)) {
    return NextResponse.next();
  }

  return NextResponse.redirect(new URL("/sign-in", request.url));
});
