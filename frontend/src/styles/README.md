# 样式文件说明

## 目录结构

```
styles/
├── views/              # 视图组件样式
│   ├── Annotate.css           # 标注页面样式
│   ├── Export.css             # 导出管理页面样式
│   ├── QualityControl.css     # 质量控制页面样式
│   ├── TaskDetail.css         # 任务详情页面样式
│   └── Tasks.css              # 任务管理页面样式
└── README.md           # 本文件
```

## 使用方式

各个Vue组件已通过import方式导入对应的样式文件：

```javascript
// 示例：TaskDetail.vue
import '@/styles/views/TaskDetail.css'
```

## 样式作用域

所有提取的样式都保持了原有的scoped作用域特性，因此不会影响其他组件。

## 优势

1. **代码分离**: Vue组件文件更简洁，逻辑和样式分离
2. **易于维护**: 样式集中管理，修改更方便
3. **提升性能**: 样式可以独立缓存和加载
4. **便于复用**: 相同的样式可以被多个组件引用

## 注意事项

- CSS文件中的`:deep()`选择器语法需要在父元素上添加上下文类名
- 例如：`.annotate-container-fullscreen :deep(.el-tabs--border-card)` 确保样式只作用于特定组件内的Element Plus组件

