# CG基础——为什么选择四元数

> 学习路线根据Scratchapixel网站来走，本blog将具体的式子变换完全列出来，以求长时间回头看内容的时候能够很快的回顾并夯实这些知识


如何描述空间内的一个向量？最符合直觉的是使用一个三元组，也就是我们所熟知的：
$$
\begin{bmatrix} x \\ y \\ z \end{bmatrix}  或者  \begin{bmatrix} x & y & z \end{bmatrix}
$$
同时三元组足够我们完整的描述一个向量了，这是我们在线性代数内学到的，同时对于这个向量的缩放，旋转，本质上也就是对这个向量左乘或右乘矩阵。

但是我们一般忽略了一点：对于线性代数来说，的确三元组足够描述一个向量的所有特征，但是在线性代数这门学科的框架内，所有的向量的起点都是原点，也就是$O$，在线性代数内，我们不关注如何平移一个向量。换句话说，我们用三元组能够完整的描述一个向量的方向，缩放，但是我们无法完整的描述这个向量的“位移”，也就是这个向量的起点在哪里。

先来看明白旋转缩放的运行规律，然后我们再来看为什么三元组无法描述向量的位移。我们此处先用三元组描述一个向量$\vec{p}$:
$$
\vec{p} = \begin{bmatrix} x & y & z \end{bmatrix}
$$

### 缩放

对于向量$\vec{p}$来说，缩放的本质就是一个常数乘以这个向量，也就是 $\vec{p'} = k\vec{p}$，其中$k$是一个常实数，我们可以对这个式子做一个变换，也就是：
$$
\vec{p'} = k\vec{p} = kI\vec{p} = k\begin{bmatrix}1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1\end{bmatrix}\vec{p} = 
\begin{bmatrix}k & 0 & 0 \\ 0 & k & 0 \\ 0 & 0 & k\end{bmatrix}\vec{p}
$$
可以发现，我们所说的缩放实际上就是一个初等变换，这跟我们在线性代数上所得到的知识是一样的。

### 旋转

在一个三维场景中，我们一般把一个复杂旋转分成三个旋转的结合：绕x轴进行旋转，绕y轴进行旋转以及绕z轴进行旋转。

我们先从绕z轴的情况入手，我们把实现放到x-y平面内，对于一个三位内的向量，我们可以暂时性的将其简化为一个二维平面内的操作。和我们在缩放内所说的一样，旋转的本质也是一个初等变换。

在二维的x-y平面内，我们假设向量$\vec{p}$是单位圆上的一个向量，那么对于$\vec{p}$我们可以用一个参数来描述：
$$
\vec{p} = \begin{bmatrix} x & y\end{bmatrix} = \begin{bmatrix}cos\alpha & sin\alpha \end{bmatrix}
$$
其中$\alpha$是向量$\vec{p}$和x轴正方向形成的夹角。我们让$\vec{p}$旋转$\theta$的角度，那么新的向量$\vec{p'}$的参数我们可以这么描述：
$$
\vec{p'} = \begin{bmatrix} x' & y'\end{bmatrix} = \begin{bmatrix}cos(\alpha + \theta) & sin(\alpha + \theta) \end{bmatrix}
$$
对于新的向量$\vec{p'}$，我们可以把式子转化一下：
$$
x'= cos(\alpha + \theta) = cos\alpha cos\theta - sin\alpha sin\theta = xcos\theta - ysin\theta \\
y'= sin(\alpha + \theta) = sin\alpha cos\theta + cos\alpha sin\theta = ycos\theta + xsin\theta
$$
我们把等式化简一下：
$$
x'=  xcos\theta - ysin\theta \\
y'= ycos\theta + xsin\theta = xsin\theta + ycos\theta
$$
这个式子我们本身就能用矩阵乘法来进行描述了，也就是
$$
\begin{bmatrix}x' & y' \end{bmatrix} =\begin{bmatrix}x & y \end{bmatrix} \begin{bmatrix}cos\theta & sin\theta \\ -sin\theta & cos\theta \end{bmatrix} = \vec{p}\begin{bmatrix}cos\theta & sin\theta \\ -sin\theta & cos\theta \end{bmatrix}
$$
所以我们最后得到的是：我们在x-y平面内把一个向量沿z轴旋转任意$\theta$角度，我们只需要用最初的向量右乘$\begin{bmatrix}cos\theta & sin\theta \\ -sin\theta & cos\theta \end{bmatrix}$矩阵就好，而反推到三维内，我们只需要把第三维的位置用单位向量对应位置的值进行填充就好，也就是$\begin{bmatrix}cos\theta & sin\theta & 0 \\ -sin\theta & cos\theta & 0 \\ 0 & 0 & 1\end{bmatrix}$

相同的，我们在绕x轴的变换矩阵和绕y轴的变换矩阵分辨可以用下面的两个矩阵来描述
$$
绕x轴:\begin{bmatrix}1 & 0 & 0 \\0 & cos\theta & sin\theta\\0 & -sin\theta & cos\theta \end{bmatrix} \\
绕y轴:\begin{bmatrix}cos\theta &0 & sin\theta\\ 0 & 1 & 0 \\ -sin\theta & 0 &cos\theta \end{bmatrix}
$$


可以用相同的方式描述出来，而在三维内的绕一个斜线进行旋转的复杂情况，我们可以将复杂的旋转分解为多个有限有序的绕x，绕y，绕z轴的旋转的变换矩阵的组合

### 平移

在上面的情况内，我们用三元组成功的描述了缩放和旋转，但是我们要如何描述一个向量的位移呢？并且这个位移我们也需要用初等变换的方式来进行实现。我们发现，我们无法用线性变换的方式来描述这个内容。我们不妨这样：我们先看下我们要做的事情是把这个点从$\begin{bmatrix}x, y, z\end{bmatrix}$移动到$\begin{bmatrix}x+a, y+b, z+c\end{bmatrix}$的位置上，实际上我们可以这么造一个等式，让其满足我们的需求：
$$
x' = x*1+y*0+z*0+a = x+a\\
y' = x*0+y*1+z*0+b = y+b\\
z' = x*0+y*0+z*1+c = z+c
$$
而我们上述式子内的$a,b,c$可以描述成$1*a, 1*b, 1*c$，代入到上式可以得到
$$
x' = x*1+y*0+z*0+1*a = x+a\\
y' = x*0+y*1+z*0+1*b = y+b\\
z' = x*0+y*0+z*1+1*c = z+c
$$
我们发现，对于这个式子，我们也完全可以用矩阵乘法的方式来进行描述：
$$
\vec{p'} = \begin{bmatrix}x & y & z & 1\end{bmatrix} \begin{bmatrix}1 & 0 & 0  \\0 & 1 & 0  \\0 & 0 & 1  \\a & b & c  \end{bmatrix}
$$
也就是说，我们给一个三维向量一个额外的第四个维度，同时我们把一个3x3的矩阵变成了一个3x4的矩阵之后，我们就能够用矩阵的初等变换来描述空间内的向量的终点的位移了，而我们在计算机图形学内，为了让整个式子更加方便我们查看，同时也为了让内存在运行的时候性能更高，我们将3x4的矩阵扩展成一个4x4的矩阵，如下所示：
$$
\begin{bmatrix}1 & 0 & 0  \\0 & 1 & 0  \\0 & 0 & 1  \\a & b & c  \end{bmatrix}→
\begin{bmatrix}1 & 0 & 0 & 0 \\0 & 1 & 0 & 0 \\0 & 0 & 1 & 0 \\a & b & c & 1 \end{bmatrix}
$$
扩展的第四列这一列向量不会干扰计算结果。

### 总结

至此，我们能够完全明白在CG内用四元组的原因，三元组能够很好的描述空间内的点的位置的缩放和旋转，但是没法描述这个点的平移情况。我们后面会将上面所说的向量给用点来代替，这只是概念的转换，对于线性代数来说，矩阵变换和我们描述的是向量还是点没有关系，但是在CG内我们需要摒弃以前的唯向量思维，我们需要考虑的是一个点在不同的坐标系内如何进行转换，以及我们如何处理这个点的位置和这个点所附加的各种属性。(关于一个点在不同的空间的坐标系内如何进行转换，可以完整观看3B1B的视频：[线性代数的本质](https://www.bilibili.com/video/BV1Ys411k7yQ) 这个视频能够帮助你建立线性代数的几何直觉，对后面的概念理解能够有非常客观的帮助)



