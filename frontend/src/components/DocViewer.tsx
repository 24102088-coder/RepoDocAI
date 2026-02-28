"use client";

import ReactMarkdown from "react-markdown";

interface Props {
  content: string;
}

export default function DocViewer({ content }: Props) {
  if (!content) {
    return <p className="text-gray-500 italic">No content available.</p>;
  }

  return (
    <ReactMarkdown
      components={{
        h1: ({ children }) => (
          <h1 className="text-3xl font-bold text-white mt-8 mb-4">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-2xl font-semibold text-gray-100 mt-6 mb-3 pb-2 border-b border-gray-700">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-xl font-semibold text-gray-200 mt-5 mb-2">{children}</h3>
        ),
        p: ({ children }) => (
          <p className="text-gray-300 leading-relaxed mb-4">{children}</p>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-inside mb-4 space-y-1 text-gray-300">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside mb-4 space-y-1 text-gray-300">{children}</ol>
        ),
        li: ({ children }) => <li className="text-gray-300">{children}</li>,
        code: ({ className, children, ...props }) => {
          const isInline = !className;
          if (isInline) {
            return (
              <code className="bg-gray-800 text-red-400 px-1.5 py-0.5 rounded text-sm">
                {children}
              </code>
            );
          }
          return (
            <code
              className="block bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm text-gray-200 mb-4"
              {...props}
            >
              {children}
            </code>
          );
        },
        pre: ({ children }) => (
          <pre className="bg-gray-900 rounded-lg overflow-x-auto mb-4">{children}</pre>
        ),
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 underline hover:text-blue-300"
          >
            {children}
          </a>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-amd-red pl-4 italic text-gray-400 my-4">
            {children}
          </blockquote>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto mb-4">
            <table className="w-full border-collapse border border-gray-700">{children}</table>
          </div>
        ),
        th: ({ children }) => (
          <th className="border border-gray-700 bg-gray-800 px-3 py-2 text-left font-semibold text-gray-200">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-gray-700 px-3 py-2 text-gray-300">{children}</td>
        ),
        strong: ({ children }) => (
          <strong className="font-semibold text-white">{children}</strong>
        ),
        em: ({ children }) => <em className="italic text-gray-400">{children}</em>,
        hr: () => <hr className="border-gray-700 my-6" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
