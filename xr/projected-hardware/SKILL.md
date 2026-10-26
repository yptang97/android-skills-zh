---
name: projected-hardware
description: 提供在 Android XR 投影设备（例如音频眼镜和显示眼镜）上访问和管理硬件的说明与工作流。
  当你在 Android 应用中为智能眼镜构建体验，并且需要访问相机、麦克风等设备硬件、处理眼镜专属的
  运行时权限，或使用 projected context 管理连接生命周期时，使用这个 skill。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-17'
  keywords:
  - Android XR
  - intelligent eyewear
  - audio glasses
  - display glasses
  - glasses hardware
  - ProjectedContext
  - projected context
  - runtime permissions
  - CameraX
  - audio recording
---

## 前置条件

- 必须使用 `compileSdk` 36 或更高版本。

## 连接与生命周期管理

只有在眼镜连接到主机手机时，才能访问智能眼镜硬件。使用
`ProjectedContext` 监控连接状态并管理资源生命周期。你必须阅读
[了解 projected activity 与 projected context](references/android/develop/xr/jetpack-xr-sdk/glasses/support-different-types.md)，以了解
如何获取 projected context，以及[如何管理它的生命周期](references/android/develop/xr/jetpack-xr-sdk/glasses/check-availability.md)。

## 请求眼镜硬件权限

- **硬件权限与选用**：你必须阅读 [请求硬件权限](references/android/develop/xr/jetpack-xr-sdk/request-hardware-permissions.md)，以了解如何在 Android 清单文件中声明相机和麦克风运行时权限、在不同场景下请求运行时权限，以及处理权限结果。

## 眼镜硬件访问与能力

- **相机拍摄与 CameraX**：你必须阅读 [用眼镜相机捕获图像](references/android/develop/xr/jetpack-xr-sdk/access-hardware-projected-context.md)，以了解使用 `ProjectedContext` 通过眼镜相机拍照的实现模式。
