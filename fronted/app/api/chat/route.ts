import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();
    
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'llama3.2',
        prompt: `You are a helpful college advisor. Answer questions about colleges, admissions, costs, programs, and student life. Be concise and helpful.

Question: ${message}
Answer:`,
        stream: false,
        options: {
          temperature: 0.4,
          max_tokens: 150
        }
      })
    });

    const data = await response.json();
    return NextResponse.json({ response: data.response || 'No response generated' });
  } catch (error) {
    return NextResponse.json({ response: 'Sorry, I cannot process your request right now.' });
  }
}