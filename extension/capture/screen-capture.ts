export interface ScreenCaptureCallbacks {
  onStart?: () => void;
  onStop?: () => void;
  onError?: (error: Error) => void;
}

export class ScreenCapture {
  private stream: MediaStream | null = null;
  private videoEl: HTMLVideoElement | null = null;
  private callbacks: ScreenCaptureCallbacks;

  constructor(callbacks: ScreenCaptureCallbacks = {}) {
    this.callbacks = callbacks;
  }

  async startCapture(): Promise<HTMLVideoElement> {
    try {
      this.stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Screen capture denied');
      this.callbacks.onError?.(error);
      throw error;
    }

    this.videoEl = document.createElement('video');
    this.videoEl.srcObject = this.stream;
    this.videoEl.muted = true;
    this.videoEl.style.display = 'none';
    document.body.appendChild(this.videoEl);
    await this.videoEl.play();

    this.stream.getVideoTracks()[0].addEventListener('ended', () => {
      this.cleanup();
      this.callbacks.onStop?.();
    });

    this.callbacks.onStart?.();
    return this.videoEl;
  }

  stopCapture(): void {
    this.cleanup();
    this.callbacks.onStop?.();
  }

  isCapturing(): boolean {
    return this.stream !== null && this.stream.active;
  }

  getVideoElement(): HTMLVideoElement | null {
    return this.videoEl;
  }

  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.videoEl) {
      this.videoEl.pause();
      this.videoEl.srcObject = null;
      this.videoEl.remove();
      this.videoEl = null;
    }
  }
}
