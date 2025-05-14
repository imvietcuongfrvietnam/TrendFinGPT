import React, { useState, useEffect } from "react";
import "../styles/Home.css";

export default function Home() {
  const [docs, setDocs] = useState([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const size = 20;

  useEffect(() => {
    async function fetchDocs() {
      try {
        const res = await fetch(
          `http://127.0.0.1:2811?page=${page}&size=${size}`
        );
        const json = await res.json();
        setDocs(json.documents);
        setPages(json.pages);
      } catch (err) {
        console.error("Failed to load docs:", err);
      }
    }
    fetchDocs();
  }, [page]);

  const renderPagination = () => {
    if (pages <= 1) return null;

    const pagesToShow = new Set();
    pagesToShow.add(1);
    pagesToShow.add(pages);
    for (let p = page - 1; p <= page + 1; p++) {
      if (p > 1 && p < pages) pagesToShow.add(p);
    }

    const sortedPages = Array.from(pagesToShow).sort((a, b) => a - b);
    const pageItems = [];

    sortedPages.forEach((p, idx) => {
      if (idx > 0 && p - sortedPages[idx - 1] > 1) {
        pageItems.push(
          <span key={`ellipsis-${p}`} className="pagination-ellipsis">
            …
          </span>
        );
      }
      pageItems.push(
        <button
          key={p}
          onClick={() => setPage(p)}
          className={
            p === page ? 'pagination-item active' : 'pagination-item'
          }
        >
          {p}
        </button>
      );
    });

    return <div className="pagination-numbers">{pageItems}</div>;
  };

  return (
    <div className="home-container">
      <ul className="home-list">
        {docs.map((doc) => {
          const hostname = new URL(doc.url).hostname;
          const faviconUrl = `https://www.google.com/s2/favicons?sz=32&domain=${hostname}`;
          return (
            <li key={doc.id} className="home-item">
              <div className="doc-meta">
                <img
                  src={faviconUrl}
                  alt={`favicon of ${hostname}`}
                  className="doc-favicon"
                />
                <span className="doc-author">{doc.author || "Unknown"}</span>
                <span className="doc-source">from {hostname}</span>
              </div>
              <a href={doc.url} target="_blank" rel="noopener noreferrer">
                <h2>{doc.title}</h2>
              </a>
              <p>{doc.summary}</p>
              <small>{doc.date}</small>
            </li>
          );
        })}
      </ul>

      {renderPagination()}
    </div>
  );
}
