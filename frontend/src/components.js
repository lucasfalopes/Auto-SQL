import React, { useState } from "react"

export const Component = () => {
    const [question, setQuestion] = useState("")
    const [sqlQuery, setSqlQuery] = useState("")
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            const response = await fetch("http://localhost:8000/api/query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ question }),
            })

            if (!response.ok) {
                throw new Error("Failed to fetch data")
            }

            const data = await response.json()
            setSqlQuery(data.query)
            setResults(data.results)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div id="webcrumbs">
            <div className="w-full flex justify-center overflow-hidden">
                <div className="w-full sm:w-[90%] md:w-[800px] bg-gradient-to-br from-neutral-50 to-neutral-100 p-4 sm:p-8 rounded-xl shadow-lg overflow-hidden">
                    <header className="mb-4 sm:mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 sm:gap-0">
                        <div className="flex items-center gap-3">
                            <div className="bg-primary-600 text-white p-2 rounded-lg">
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    className="h-6 w-6"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                >
                                    <path
                                        fillRule="evenodd"
                                        d="M5 4a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H5zm0 2a1 1 0 00-1 1v6a1 1 0 001 1h10a1 1 0 001-1V7a1 1 0 00-1-1H5z"
                                        clipRule="evenodd"
                                    />
                                    <path
                                        fillRule="evenodd"
                                        d="M7 9a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-800 mb-2">SQL Query Generator</h1>
                                <p className="text-neutral-600">
                                    Ask questions in natural language to generate SQL queries
                                </p>
                            </div>
                        </div>
                    </header>

                    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-4 sm:p-6 mb-4 sm:mb-6 transition-all duration-300 hover:shadow-lg">
                        <div className="relative mb-3 sm:mb-4">
                            <input
                                type="text"
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                placeholder="Ask a question (e.g., Which action movies were rented in April 2023?)"
                                className="w-full p-2 sm:p-3 pr-12 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-400 outline-none transition-all duration-200"
                            />
                        </div>

                        <button 
                            type="submit"
                            className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-4 rounded-lg transition-all duration-300 transform hover:translate-y-[-2px] hover:shadow-md flex items-center justify-center gap-2 relative z-10"
                            disabled={loading}
                        >
                            {loading ? (
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : (
                                <>
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        className="h-5 w-5"
                                        viewBox="0 0 20 20"
                                        fill="currentColor"
                                    >
                                        <path
                                            fillRule="evenodd"
                                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
                                            clipRule="evenodd"
                                        />
                                    </svg>
                                    Ask
                                </>
                            )}
                        </button>
                    </form>

                    {error && (
                        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
                            {error}
                        </div>
                    )}

                    {sqlQuery && (
                        <div className="mb-4 sm:mb-6 overflow-hidden bg-neutral-900 rounded-lg shadow-md">
                            <div className="p-3 bg-neutral-800 text-neutral-300 text-sm flex justify-between items-center relative z-10">
                                <span className="font-medium">Generated SQL Query</span>
                                <button 
                                    className="text-neutral-400 hover:text-white transition-colors hover:scale-105 transition-transform duration-300 ease-in-out"
                                    onClick={() => navigator.clipboard.writeText(sqlQuery)}
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        className="h-5 w-5"
                                        viewBox="0 0 20 20"
                                        fill="currentColor"
                                    >
                                        <path d="M8 2a1 1 0 000 2h2a1 1 0 100-2H8z" />
                                        <path d="M3 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v6h-4.586l1.293-1.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L10.414 13H15v3a2 2 0 01-2 2H5a2 2 0 01-2-2V5zM15 11h2a1 1 0 110 2h-2v-2z" />
                                    </svg>
                                </button>
                            </div>
                            <pre className="p-2 sm:p-4 text-gray-300 text-xs sm:text-sm overflow-x-auto">
                                <code className="language-sql">
                                    {sqlQuery}
                                </code>
                            </pre>
                        </div>
                    )}

                    {results.length > 0 && (
                        <div className="relative bg-white rounded-lg shadow-md p-3 sm:p-4 overflow-hidden">
                            <div className="mb-3 flex justify-between items-center">
                                <h2 className="text-lg font-semibold text-gray-800">Query Results</h2>
                                <div className="flex flex-wrap gap-2 z-20 relative">
                                    <button 
                                        className="text-neutral-500 hover:text-neutral-700 transition-colors flex items-center gap-1 py-1 px-2 rounded hover:bg-neutral-100 text-xs sm:text-sm"
                                        onClick={() => {
                                            const csv = results.map(row => row.join(',')).join('\n')
                                            navigator.clipboard.writeText(csv)
                                        }}
                                    >
                                        <svg
                                            xmlns="http://www.w3.org/2000/svg"
                                            className="h-4 w-4 sm:h-5 sm:w-5"
                                            viewBox="0 0 20 20"
                                            fill="currentColor"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                        <span className="text-xs sm:text-sm">CSV</span>
                                    </button>
                                </div>
                            </div>

                            <div className="max-h-[200px] sm:max-h-[300px] overflow-y-auto rounded-lg border border-neutral-200 relative z-10">
                                <table className="min-w-full divide-y divide-gray-200 text-xs sm:text-sm">
                                    <thead className="bg-gray-50 sticky top-0 z-10">
                                        <tr>
                                            {results[0]?.map((_, index) => (
                                                <th
                                                    key={index}
                                                    scope="col"
                                                    className="px-3 py-2 sm:px-6 sm:py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider"
                                                >
                                                    Column {index + 1}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-neutral-200">
                                        {results.map((row, rowIndex) => (
                                            <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
                                                {row.map((cell, cellIndex) => (
                                                    <td 
                                                        key={cellIndex}
                                                        className="px-3 py-2 sm:px-6 sm:py-4 whitespace-nowrap text-xs sm:text-sm text-gray-900"
                                                    >
                                                        {cell}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
} 