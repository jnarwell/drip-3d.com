import { useState, useEffect } from 'react';
import { getMarkdownPath } from '../config/docsNav';

export interface DocFrontmatter {
  title?: string;
  description?: string;
  [key: string]: unknown;
}

export interface UseDocsResult {
  content: string;
  frontmatter: DocFrontmatter;
  loading: boolean;
  error: string | null;
}

// Simple YAML frontmatter parser for browser
function parseFrontmatter(markdown: string): { content: string; frontmatter: DocFrontmatter } {
  const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/;
  const match = markdown.match(frontmatterRegex);

  if (!match) {
    return { content: markdown, frontmatter: {} };
  }

  const frontmatterStr = match[1];
  const content = markdown.slice(match[0].length);
  const frontmatter: DocFrontmatter = {};

  // Simple YAML parser for key: value pairs
  const lines = frontmatterStr.split('\n');
  for (const line of lines) {
    const colonIdx = line.indexOf(':');
    if (colonIdx > 0) {
      const key = line.slice(0, colonIdx).trim();
      let value = line.slice(colonIdx + 1).trim();
      // Remove quotes if present
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      frontmatter[key] = value;
    }
  }

  return { content, frontmatter };
}

export function useDocs(routePath: string): UseDocsResult {
  const [content, setContent] = useState<string>('');
  const [frontmatter, setFrontmatter] = useState<DocFrontmatter>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchDoc() {
      setLoading(true);
      setError(null);

      const mdPath = getMarkdownPath(routePath);

      try {
        const response = await fetch(mdPath);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Document not found');
          }
          throw new Error(`Failed to load document: ${response.status}`);
        }

        // Check content-type - Vite returns HTML for missing files (SPA fallback)
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('text/html')) {
          throw new Error('Document not found');
        }

        const text = await response.text();

        if (cancelled) return;

        // Additional check: if it looks like HTML, it's the fallback
        if (text.trimStart().startsWith('<!DOCTYPE') || text.trimStart().startsWith('<html')) {
          throw new Error('Document not found');
        }

        const { content: parsedContent, frontmatter: parsedFrontmatter } = parseFrontmatter(text);
        setContent(parsedContent);
        setFrontmatter(parsedFrontmatter);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Unknown error');
        setContent('');
        setFrontmatter({});
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchDoc();

    return () => {
      cancelled = true;
    };
  }, [routePath]);

  return { content, frontmatter, loading, error };
}
