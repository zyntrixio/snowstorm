<script lang="ts">
  import { onMount } from "svelte";
  import UserStats from "./UserStats.svelte";

  enum BundleIds {
    "com.lloyds.api2" = "Lloyds",
    "com.halifax.api2" = "Halifax",
    "com.bos.api2" = "Bank of Scotland",
    "total" = "Total",
  }

  enum CardStatus {
    "success" = "Active",
    "pending" = "Pending",
    "failed" = "Failed",
  }

  type Retailer = {
    [key: string]: {
      [key: string]: number;
    };
  };

  type StatusLoyaltyAccountsByChannel = {
    [key: string]: {
      [key: string]: number;
    };
  };

  type LBGStats = {
    api_stats: {
      calls: number;
      deletions: {
        [key: string]: number;
      };
      percentiles: {
        p50: number;
        p75: number;
        p90: number;
      };
      status_codes: {
        [key: string]: number;
      };
    };
    checkly: number;
    loyalty_accounts: {
      failed: Retailer;
      pending: Retailer;
      success: Retailer;
    };
    payment_accounts: {
      failed: Retailer;
      pending: Retailer;
      success: Retailer;
    };
    users: {
      [key: string]: number;
    };
  };

  let lbgStats: LBGStats = {
    api_stats: {
      calls: 0,
      deletions: {},
      percentiles: {
        p50: 0,
        p75: 0,
        p90: 0,
      },
      status_codes: {},
    },
    checkly: 0,
    loyalty_accounts: {
      failed: {},
      pending: {},
      success: {},
    },
    payment_accounts: {
      failed: {},
      pending: {},
      success: {},
    },
    users: {},
  };

  let activeLoyaltyAccountsByChannel = {},
    pendingLoyaltyAccountsByChannel = {},
    failedLoyaltyAccountsByChannel = {};
  let selectedFilter = "all";
  let isLoaded = false;

  function sortByChannel(
    statusLoyaltyAccountsByChannel: StatusLoyaltyAccountsByChannel
  ) {
    // Lucky that the desired order is reverse-alphabetical this may not always be the case
    return Object.entries(statusLoyaltyAccountsByChannel)
      .sort((a, b) => {
        return a[0] < b[0] ? 1 : -1;
      })
      .reduce((acc, [channel, retailers]) => {
        acc[channel] = retailers;
        return acc;
      }, {});
  }

  function swapChannelAndRetailer(
    statusLoyaltyAccountsByChannel: StatusLoyaltyAccountsByChannel
  ) {
    return Object.entries(statusLoyaltyAccountsByChannel).reduce(
      (acc, [retailers, channel]) => {
        Object.entries(channel).forEach(([channelName, count]) => {
          if (!acc[channelName]) {
            acc[channelName] = {};
          }
          acc[channelName][retailers] = count;
        });
        return acc;
      },
      {}
    );
  }

  function addTotalToEachChannel(
    statusLoyaltyAccountsByChannel: StatusLoyaltyAccountsByChannel
  ) {
    Object.entries(statusLoyaltyAccountsByChannel).forEach(
      ([channel, retailers]) => {
        statusLoyaltyAccountsByChannel[channel]["total"] = Object.values(
          retailers
        ).reduce((acc, count) => acc + count, 0);
      }
    );
    return statusLoyaltyAccountsByChannel;
  }

  async function fetchLBGStats() {
    const response = await fetch(
      "https:stats.gb.bink.com/lbg/api?auth=4e97f9c1-c259-4858-99d4-191800b75946"
    );
    const data = await response.json();
    lbgStats = data;
    activeLoyaltyAccountsByChannel = addTotalToEachChannel(
      sortByChannel(swapChannelAndRetailer(lbgStats.loyalty_accounts.success))
    );
    pendingLoyaltyAccountsByChannel = addTotalToEachChannel(
      sortByChannel(swapChannelAndRetailer(lbgStats.loyalty_accounts.pending))
    );
    failedLoyaltyAccountsByChannel = addTotalToEachChannel(
      sortByChannel(swapChannelAndRetailer(lbgStats.loyalty_accounts.failed))
    );
    isLoaded = true;
  }

  onMount(() => {
    fetchLBGStats();
    const interval = setInterval(() => {
      fetchLBGStats();
    }, 30000);

    return () => {
      clearInterval(interval);
    };
  });

  export function titleCase(string: string) {
    return string[0].toUpperCase() + string.substr(1).toLowerCase();
  }
</script>

<main>
  <div class="header">
    <img src="https://bink.com/wp-content/uploads/2023/02/logosite.png" alt="Bink" />
    <select id="channel-select" bind:value={selectedFilter}>
      <option value="all">LBG Stats</option>
      <option value="com.lloyds.api2">Lloyds</option>
      <option value="com.halifax.api2">Halifax</option>
      <option value="com.bos.api2">Bank of Scotland</option>
    </select>
  </div>

  {#if isLoaded}
    <div class="content">
      <div class="column big-column">
        <section id="loyalty-cards-stats">
          <h2>Loyalty Cards</h2>
          <table>
            <thead>
              <tr>
                <th>Channel</th>
                <th>Retailer</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              <!-- Active -->
              <tr>
                <td class="table-subheading" colspan="2"
                  ><strong>Active</strong></td
                >
              </tr>
              {#each Object.entries(activeLoyaltyAccountsByChannel) as [channel, channelRetailers]}
                {#each Object.entries(channelRetailers) as [retailer, count]}
                  {#if retailer !== "total" && (selectedFilter === "all" || selectedFilter === channel)}
                    <tr>
                      <td>{BundleIds[channel]}</td>
                      <td>{titleCase(retailer)}</td>
                      <td>{count}</td>
                    </tr>
                  {/if}
                {/each}
              {/each}
              <tr>
                <td><strong>Total</strong></td>
                <td />
                <td>
                  <strong>
                    {#if selectedFilter === "all"}
                      {lbgStats.loyalty_accounts.success.total}
                    {:else}
                      {activeLoyaltyAccountsByChannel[selectedFilter]?.total ||
                        0}
                    {/if}
                  </strong>
                </td>
              </tr>
              <!-- Pending -->
              <tr>
                <td class="table-subheading" colspan="2"
                  ><strong>Pending</strong></td
                >
              </tr>
              {#each Object.entries(pendingLoyaltyAccountsByChannel) as [channel, channelRetailers]}
                {#each Object.entries(channelRetailers) as [retailer, count]}
                  {#if retailer !== "total" && (selectedFilter === "all" || selectedFilter === channel)}
                    <tr>
                      <td>{BundleIds[channel]}</td>
                      <td>{titleCase(retailer)}</td>
                      <td>{count}</td>
                    </tr>
                  {/if}
                {/each}
              {/each}
              <tr>
                <td><strong>Total</strong></td>
                <td />
                <td>
                  <strong>
                    {#if selectedFilter === "all"}
                      {lbgStats.loyalty_accounts.pending.total}
                    {:else}
                      {pendingLoyaltyAccountsByChannel[selectedFilter]?.total ||
                        "0"}
                    {/if}
                  </strong>
                </td>
              </tr>
              <!-- Failed -->
              <tr>
                <td class="table-subheading" colspan="2"><b>Failed</b></td>
              </tr>
              {#each Object.entries(failedLoyaltyAccountsByChannel) as [channel, channelRetailers]}
                {#each Object.entries(channelRetailers) as [retailer, count]}
                  {#if retailer !== "total" && (selectedFilter === "all" || selectedFilter === channel)}
                    <tr>
                      <td>{BundleIds[channel]}</td>
                      <td>{titleCase(retailer)}</td>
                      <td>{count}</td>
                    </tr>
                  {/if}
                {/each}
              {/each}
              <tr>
                <td><strong>Total</strong></td>
                <td />
                <td>
                  <strong>
                    {#if selectedFilter === "all"}
                      {lbgStats.loyalty_accounts.failed.total}
                    {:else}
                      {failedLoyaltyAccountsByChannel[selectedFilter]?.total ||
                        0}
                    {/if}
                  </strong>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
        <section id="payment-cards-stats">
          <h2>Payment Cards</h2>
          <table>
            <thead>
              <tr>
                <th>Channel</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {#each Object.entries(lbgStats.payment_accounts) as [status, count]}
                <tr>
                  <td class="table-subheading" colspan="2"
                    ><b>{titleCase(CardStatus[status])}</b></td
                  >
                </tr>
                {#if !Object.keys(lbgStats.payment_accounts[status]).includes(selectedFilter) && selectedFilter !== "all"}
                  <tr><td>{BundleIds[selectedFilter]}</td><td>0</td></tr>
                {:else}
                  {#each Object.entries(lbgStats.payment_accounts[status]) as [channel, count]}
                    {#if selectedFilter === "all" || selectedFilter === channel}
                      <tr>
                        <td
                          >{@html channel === "total"
                            ? `<strong>${BundleIds[channel]}</strong>`
                            : BundleIds[channel]}</td
                        >
                        <td
                          >{@html channel === "total"
                            ? `<strong>${count}</strong>`
                            : count}</td
                        >
                      </tr>
                    {/if}
                  {/each}
                {/if}
              {/each}
            </tbody>
          </table>
          <UserStats
            users={lbgStats.users}
            isLargeViewportRendered={true}
            {selectedFilter}
          />
        </section>
      </div>
      <div class="column small-column">
        <UserStats
          users={lbgStats.users}
          isLargeViewportRendered={false}
          {selectedFilter}
        />
        <section id="deleted-accounts">
          <h2>Deleted Accounts & Cards</h2>
          <table>
            <thead>
              <th>Endpoint</th>
              <th>Count</th>
            </thead>
            <tbody>
              {#each Object.entries(lbgStats.api_stats.deletions) as [endpoint, count]}
                <tr>
                  <td>{endpoint}</td>
                  <td>{count}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </section>
        <section id="api-stats">
          <h2>API Stats</h2>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Availability</td>
                <td>{Math.round(lbgStats?.checkly * 100) / 100}%</td>
              </tr>
              <tr>
                <td>Total Calls</td>
                <td>{lbgStats.api_stats.calls}</td>
              </tr>
            </tbody>
          </table>
          <table>
            <thead>
              <th>Percentile</th>
              <th>Value</th>
            </thead>
            <tbody>
              {#each Object.entries(lbgStats.api_stats.percentiles) as [percentage, value]}
                <tr>
                  <td>{percentage.toUpperCase()}</td>
                  <td>{value}s</td>
                </tr>
              {/each}
            </tbody>
          </table>
          <table>
            <thead>
              <th>Status Code</th>
              <th>Count</th>
            </thead>
            <tbody>
              {#each Object.entries(lbgStats.api_stats.status_codes) as [code, value]}
                <tr>
                  <td>{code}</td>
                  <td>{value}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  {/if}
</main>

<style>
  .header {
    display: flex;
    flex-direction: column;
    flex: 1;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
  }

  .header img {
    height: 70px;
  }
  .content {
    display: flex;
    width: 100%;
    flex-direction: row;
    justify-content: center;
  }
  .column {
    text-align: center;
    border-radius: 10px;
    width: 560px;
  }

  .small-column {
    width: 400px;
    display: flex;
    flex-direction: column;
    font-size: 0.9rem;
  }

  .big-column {
    width: 1000px;
    display: flex;
    flex: space-between;
  }

  .big-column section {
    width: 100%;
  }

  .table-subheading {
    padding-top: 25px;
  }

  #api-stats table {
    margin-bottom: 30px;
  }

  @media only screen and (max-width: 1416px) {
    .big-column {
      flex-direction: column;
      width: 500px;
    }
    .small-column {
      gap: 32px;
      font-size: 1rem;
    }
  }
</style>
