"""Real-ESRGAN super-resolution (CPU, PyTorch) — minimal re-implementation of the two public architectures.
Weights (BSD-3, xinntao/Real-ESRGAN releases): realesr-general-x4v3.pth (SRVGGNetCompact), RealESRGAN_x4plus.pth (RRDBNet).
Usage: python3 sr.py <model.pth> <in_dir> <out_dir> [--tile 384]"""
import sys, os, glob, time, torch, numpy as np
import torch.nn as nn, torch.nn.functional as F
from PIL import Image

class SRVGG(nn.Module):
    def __init__(s, nf=64, nc=32, up=4):
        super().__init__(); s.up = up
        b = [nn.Conv2d(3, nf, 3, 1, 1), nn.PReLU(nf)]
        for _ in range(nc): b += [nn.Conv2d(nf, nf, 3, 1, 1), nn.PReLU(nf)]
        b += [nn.Conv2d(nf, 3 * up * up, 3, 1, 1)]
        s.body = nn.ModuleList(b); s.ps = nn.PixelShuffle(up)
    def forward(s, x):
        o = x
        for m in s.body: o = m(o)
        return s.ps(o) + F.interpolate(x, scale_factor=s.up, mode='nearest')

class RDB(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__()
        s.conv1 = nn.Conv2d(nf, gc, 3, 1, 1); s.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        s.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1); s.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        s.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1); s.l = nn.LeakyReLU(0.2, True)
    def forward(s, x):
        x1 = s.l(s.conv1(x)); x2 = s.l(s.conv2(torch.cat((x, x1), 1)))
        x3 = s.l(s.conv3(torch.cat((x, x1, x2), 1))); x4 = s.l(s.conv4(torch.cat((x, x1, x2, x3), 1)))
        return s.conv5(torch.cat((x, x1, x2, x3, x4), 1)) * 0.2 + x
class RRDB(nn.Module):
    def __init__(s, nf=64): super().__init__(); s.rdb1, s.rdb2, s.rdb3 = RDB(nf), RDB(nf), RDB(nf)
    def forward(s, x): return s.rdb3(s.rdb2(s.rdb1(x))) * 0.2 + x
class RRDBNet(nn.Module):
    def __init__(s, nf=64, nb=23):
        super().__init__()
        s.conv_first = nn.Conv2d(3, nf, 3, 1, 1); s.body = nn.Sequential(*[RRDB(nf) for _ in range(nb)])
        s.conv_body = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_last = nn.Conv2d(nf, 3, 3, 1, 1); s.l = nn.LeakyReLU(0.2, True)
    def forward(s, x):
        f = s.conv_first(x); f = f + s.conv_body(s.body(f))
        f = s.l(s.conv_up1(F.interpolate(f, scale_factor=2, mode='nearest')))
        f = s.l(s.conv_up2(F.interpolate(f, scale_factor=2, mode='nearest')))
        return s.conv_last(s.l(s.conv_hr(f)))

def load(path):
    sd = torch.load(path, map_location='cpu', weights_only=True)
    sd = sd.get('params_ema', sd.get('params', sd))
    net = SRVGG() if 'body.0.weight' in sd else RRDBNet()
    net.load_state_dict(sd, strict=True); return net.eval()

@torch.no_grad()
def upscale(net, img, tile=384, pad=16):
    x = torch.from_numpy(np.asarray(img.convert('RGB'), np.float32) / 255).permute(2, 0, 1)[None]
    _, _, h, w = x.shape; out = torch.zeros(1, 3, h * 4, w * 4)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            ys, xs = max(0, y0 - pad), max(0, x0 - pad); ye, xe = min(h, y0 + tile + pad), min(w, x0 + tile + pad)
            o = net(x[:, :, ys:ye, xs:xe])
            oy, ox = (y0 - ys) * 4, (x0 - xs) * 4; th, tw = (min(h, y0 + tile) - y0) * 4, (min(w, x0 + tile) - x0) * 4
            out[:, :, y0 * 4:y0 * 4 + th, x0 * 4:x0 * 4 + tw] = o[:, :, oy:oy + th, ox:ox + tw]
    return Image.fromarray((out[0].clamp(0, 1).permute(1, 2, 0).numpy() * 255 + 0.5).astype(np.uint8))

if __name__ == '__main__':
    model, src, dst = sys.argv[1:4]; tile = int(sys.argv[sys.argv.index('--tile') + 1]) if '--tile' in sys.argv else 384
    torch.set_num_threads(os.cpu_count()); net = load(model); os.makedirs(dst, exist_ok=True)
    fs = sorted(glob.glob(os.path.join(src, '*.png')))
    for i, f in enumerate(fs):
        o = os.path.join(dst, os.path.basename(f))
        if os.path.exists(o): continue
        t = time.time(); upscale(net, Image.open(f), tile).save(o)
        print(f'{i + 1}/{len(fs)} {os.path.basename(f)} {time.time() - t:.1f}s', flush=True)
