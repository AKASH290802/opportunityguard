'''OpportunityGuard AI - hosted agent entry point.'''

from uagents import Agent

from protocols import protocol

agent = Agent()
agent.include(protocol, publish_manifest=True)

if __name__ == '__main__':
    agent.run()
