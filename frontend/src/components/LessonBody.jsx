import { Fragment } from "react";

// Groups consecutive list items into one <ul>/<ol>; everything else maps 1:1 to a block.
export function groupBlocks(blocks) {
  const out = [];
  for (const b of blocks) {
    const last = out[out.length - 1];
    if (b.t === "li") {
      const tag = b.ordered ? "ol" : "ul";
      if (last && last.t === "list" && last.tag === tag) last.items.push(b.text);
      else out.push({ t: "list", tag, items: [b.text] });
    } else out.push(b);
  }
  return out;
}

export default function LessonBody({ blocks }) {
  return (
    <div className="lesson-body">
      {groupBlocks(blocks).map((b, i) => {
        if (b.t === "h") {
          const H = `h${Math.min(Math.max(b.level, 3), 5)}`;
          return <H key={i}>{b.text}</H>;
        }
        if (b.t === "p") return <p key={i}>{b.text}</p>;
        if (b.t === "code") return <pre key={i}>{b.text}</pre>;
        if (b.t === "list") {
          const T = b.tag;
          return <T key={i}>{b.items.map((t, j) => <li key={j}>{t}</li>)}</T>;
        }
        if (b.t === "table") {
          return (
            <div className="table-wrap" key={i}>
              <table>
                <tbody>
                  {b.rows.map((r, ri) => (
                    <tr key={ri}>{r.map((c, ci) => <td key={ci}>{c}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return <Fragment key={i} />;
      })}
    </div>
  );
}
