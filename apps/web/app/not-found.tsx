import Link from "next/link";

export default function NotFound() {
  return (
    <div className="errpage">
      <div>
        <h1>Nothing here</h1>
        <p>That canvas may have been deleted, or the link is wrong.</p>
        <Link className="btn lg primary" href="/">Back to your canvases</Link>
      </div>
    </div>
  );
}
