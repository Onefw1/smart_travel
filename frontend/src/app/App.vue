<template>
  <header class="site-header">
    <RouterLink to="/" class="brand" aria-label="智游北京首页">
      <span class="brand-mark" aria-hidden="true">京</span>
      <span>智游北京<small>BEIJING, AT YOUR PACE</small></span>
    </RouterLink>
    <span class="header-note">一城风景，随心而行</span>
  </header>
  <main><RouterView :key="$route.path" /></main>
  <footer class="site-footer">智游北京 · 课程旅行规划项目</footer>
</template>
