<script lang="ts">
  export let users: { [key: string]: number };
  export let isLargeViewportRendered: boolean;
  export let selectedFilter: string;

  let sectionClass = isLargeViewportRendered // isLargeViewportRendered hides or shows the section based on the viewport size
    ? "large-viewport"
    : "small-viewport";
</script>

<section id={sectionClass}>
  <h2>User Stats</h2>
  <table>
    <thead>
      <tr>
        <th>Channel</th>
        <th>Count</th>
      </tr>
    </thead>
    <tbody>
      {#if selectedFilter === "all" || selectedFilter === "com.lloyds.api2"}
        <tr>
          <td>Lloyds</td>
          <td>{users["com.lloyds.api2"]}</td>
        </tr>
      {/if}
      {#if selectedFilter === "all" || selectedFilter === "com.bos.api2"}
        <tr>
          <td>Bank of Scotland</td>
          <td>{users["com.bos.api2"]}</td>
        </tr>
      {/if}
      {#if selectedFilter === "all" || selectedFilter === "com.halifax.api2"}
        <tr>
          <td>Halifax</td>
          <td>{users["com.halifax.api2"]}</td>
        </tr>
      {/if}
      {#if selectedFilter === "all"}
        <tr>
          <td><b>Total</b></td>
          <td><strong>{users.total}</strong></td>
        </tr>
      {/if}
    </tbody>
  </table>
</section>

<style>
  #large-viewport {
    display: block;
  }

  #small-viewport {
    display: none;
  }

  @media only screen and (max-width: 1416px) {
    #large-viewport {
      display: none;
    }
    #small-viewport {
      display: block;
    }
  }
</style>
