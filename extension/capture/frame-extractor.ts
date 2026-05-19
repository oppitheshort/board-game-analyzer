export class FrameExtractor {
  private canvas: OffscreenCanvas | null = null;
  private ctx: OffscreenCanvasRenderingContext2D | null = null;
  private rafId: number | null = null;
  private lastFrameTime = 0;
  private lastHash = '';
  private interval: number;
  private video: HTMLVideoElement | null = null;
  private onFrame: ((data: ImageData) => void) | null = null;

  constructor(interval = 1500) {
    this.interval = interval;
  }

  start(video: HTMLVideoElement, onFrame: (data: ImageData) => void): void {
    this.video = video;
    this.onFrame = onFrame;
    this.canvas = new OffscreenCanvas(video.videoWidth || 1920, video.videoHeight || 1080);
    this.ctx = this.canvas.getContext('2d')!;
    this.lastFrameTime = 0;
    this.tick(performance.now());
  }

  stop(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.video = null;
    this.onFrame = null;
  }

  private tick = (now: number): void => {
    if (!this.video || !this.onFrame) return;

    if (now - this.lastFrameTime >= this.interval) {
      this.lastFrameTime = now;
      this.extractFrame();
    }

    this.rafId = requestAnimationFrame(this.tick);
  };

  private extractFrame(): void {
    if (!this.video || !this.ctx || !this.canvas || !this.onFrame) return;

    const w = this.video.videoWidth;
    const h = this.video.videoHeight;
    if (w === 0 || h === 0) return;

    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
    }

    this.ctx.drawImage(this.video, 0, 0, w, h);
    const imageData = this.ctx.getImageData(0, 0, w, h);

    const hash = this.computeHash(imageData);
    if (hash === this.lastHash) return;
    this.lastHash = hash;

    this.onFrame(imageData);
  }

  private computeHash(imageData: ImageData): string {
    const { data, width, height } = imageData;
    const step = Math.max(1, Math.floor((width * height) / 100));
    let hash = 0;
    for (let i = 0; i < data.length; i += step * 4) {
      hash = ((hash << 5) - hash + data[i] + data[i + 1] + data[i + 2]) | 0;
    }
    return hash.toString(36);
  }
}
