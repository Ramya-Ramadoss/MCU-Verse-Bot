import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownProps {
  content: string;
}

export const Markdown: React.FC<MarkdownProps> = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-3 leading-relaxed last:mb-0">{children}</p>,
        h1: ({ children }) => <h1 className="text-xl font-bold font-tech text-jarvis-cyan mt-4 mb-2">{children}</h1>,
        h2: ({ children }) => <h2 className="text-lg font-semibold font-tech text-jarvis-blue mt-3 mb-2">{children}</h2>,
        h3: ({ children }) => <h3 className="text-base font-medium font-tech text-jarvis-gold mt-2 mb-1">{children}</h3>,
        ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="text-jarvis-text">{children}</li>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-jarvis-cyan bg-slate-900/40 pl-3 py-1 pr-1 italic mb-3">
            {children}
          </blockquote>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-3 border border-jarvis-border rounded">
            <table className="min-w-full divide-y divide-jarvis-border">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-[#061224]/80">{children}</thead>,
        tbody: ({ children }) => <tbody className="divide-y divide-[#061224]/40">{children}</tbody>,
        tr: ({ children }) => <tr className="hover:bg-slate-900/20">{children}</tr>,
        th: ({ children }) => <th className="px-4 py-2 text-left text-xs font-semibold text-jarvis-cyan font-tech tracking-wider">{children}</th>,
        td: ({ children }) => <td className="px-4 py-2 text-sm text-jarvis-text">{children}</td>,
        code: ({ className, children, ...props }) => {
          const match = /language-(\w+)/.exec(className || '');
          const inline = !match;
          return inline ? (
            <code className="bg-[#061224] text-jarvis-gold px-1.5 py-0.5 rounded font-mono text-xs" {...props}>
              {children}
            </code>
          ) : (
            <pre className="bg-[#061224] border border-jarvis-border p-3 rounded font-mono text-xs overflow-x-auto my-3">
              <code className="text-jarvis-cyan" {...props}>{children}</code>
            </pre>
          );
        }
      }}
    >
      {content}
    </ReactMarkdown>
  );
};
export default Markdown;
