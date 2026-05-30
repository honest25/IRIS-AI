/**
 * IRIS AI — WebSocket Client
 * Singleton manager with auto-reconnect, event emitter, and message routing.
 */

type EventHandler = (data: unknown) => void;

class IRISWebSocket {
  private ws: WebSocket | null = null;
  private url: string = "";
  private listeners: Map<string, EventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isIntentionalClose = false;

  connect(deviceId: string, token: string): void {
    const wsBase =
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";
    this.url = `${wsBase}/ws/${deviceId}?token=${token}`;
    this.isIntentionalClose = false;
    this._connect();
  }

  private _connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this._emit("connected", {});
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const type = data.type || "unknown";
        this._emit(type, data);
        this._emit("*", data); // wildcard listeners
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onclose = (event) => {
      this._emit("disconnected", { code: event.code });
      if (!this.isIntentionalClose) this._scheduleReconnect();
    };

    this.ws.onerror = () => {
      this._emit("error", { message: "WebSocket error" });
    };
  }

  private _scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this._emit("max_retries", {});
      return;
    }
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => this._connect(), delay);
    this._emit("reconnecting", { attempt: this.reconnectAttempts, delay });
  }

  disconnect(): void {
    this.isIntentionalClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  send(data: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  sendVoiceCommand(text: string, conversationId?: number): void {
    this.send({
      type: "voice_command",
      content: text,
      conversation_id: conversationId,
    });
  }

  sendTelemetry(data: object): void {
    this.send({ type: "telemetry", data });
  }

  on(event: string, handler: EventHandler): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(handler);
    // Return unsubscribe function
    return () => this.off(event, handler);
  }

  off(event: string, handler: EventHandler): void {
    const handlers = this.listeners.get(event) || [];
    this.listeners.set(
      event,
      handlers.filter((h) => h !== handler)
    );
  }

  private _emit(event: string, data: unknown): void {
    (this.listeners.get(event) || []).forEach((h) => h(data));
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const wsClient = new IRISWebSocket();
