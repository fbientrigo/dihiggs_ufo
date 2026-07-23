#include "Pythia8/Pythia.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace Pythia8;

struct Channel {
  double br;
  std::vector<int> daughters;
};

static std::string jsonString(const std::string& value) {
  std::string out = "\"";
  for (char c : value) {
    if (c == '\\' || c == '"') out += '\\';
    out += c;
  }
  return out + "\"";
}

static std::string usage() {
  return "usage: pack_aa_driver --lhe FILE --out JSONL --events N --seed N "
         "--mass GEV --ctau MM --is-resonance 0|1 --production-events N "
         "--channels BR:PDG,PDG[;...]";
}

static std::string value(int argc, char** argv, const std::string& key) {
  for (int i = 1; i + 1 < argc; ++i)
    if (argv[i] == key) return argv[i + 1];
  throw std::runtime_error("missing " + key + "\n" + usage());
}

static bool hasArg(int argc, char** argv, const std::string& key) {
  for (int i = 1; i < argc; ++i) if (argv[i] == key) return true;
  return false;
}

static std::vector<Channel> parseChannels(const std::string& text) {
  std::vector<Channel> channels;
  std::stringstream all(text);
  std::string item;
  while (std::getline(all, item, ';')) {
    std::stringstream fields(item);
    std::string brText, pdgText;
    if (!std::getline(fields, brText, ':') || !std::getline(fields, pdgText))
      throw std::runtime_error("bad channel: " + item);
    Channel channel{std::stod(brText), {}};
    std::stringstream pdgs(pdgText);
    std::string pdg;
    while (std::getline(pdgs, pdg, ',')) channel.daughters.push_back(std::stoi(pdg));
    if (channel.daughters.empty()) throw std::runtime_error("empty channel: " + item);
    channels.push_back(channel);
  }
  if (channels.empty()) throw std::runtime_error("no decay channels");
  return channels;
}

// Kept separate from the event loop so the truth record remains explicit.
static void writeH2(std::ostream& out, const Event& event, const Particle& p,
                    const std::vector<int>& direct, const Channel& configured,
                    bool first) {
  if (!first) out << ',';
  const double dx = p.xDec() - p.xProd();
  const double dy = p.yDec() - p.yProd();
  const double dz = p.zDec() - p.zProd();
  const double labLength = std::sqrt(dx * dx + dy * dy + dz * dz);
  const double betaGamma = p.m() > 0.0 ? p.pAbs() / p.m() : 0.0;
  const double properLength = betaGamma > 0.0 ? labLength / betaGamma : labLength;
  out << "{\"index\":" << p.index()
      << ",\"id\":" << p.id()
      << ",\"status\":" << p.status()
      << ",\"mother1\":" << p.mother1()
      << ",\"mother2\":" << p.mother2()
      << ",\"px\":" << p.px()
      << ",\"py\":" << p.py()
      << ",\"pz\":" << p.pz()
      << ",\"e\":" << p.e()
      << ",\"m\":" << p.m()
      << ",\"hasVertex\":" << (p.hasVertex() ? "true" : "false")
      << ",\"xProd\":" << p.xProd()
      << ",\"yProd\":" << p.yProd()
      << ",\"zProd\":" << p.zProd()
      << ",\"tProd\":" << p.tProd()
      << ",\"xDec\":" << p.xDec()
      << ",\"yDec\":" << p.yDec()
      << ",\"zDec\":" << p.zDec()
      << ",\"tDec\":" << p.tDec()
      << ",\"properTime_mm\":" << p.tau()
      << ",\"labLength_mm\":" << labLength
      << ",\"properLength_mm\":" << properLength
      << ",\"beforeStatus\":1"
      << ",\"directDaughters\":[";
  for (std::size_t i = 0; i < direct.size(); ++i) {
    if (i) out << ',';
    out << direct[i];
  }
  out << "],\"configuredDaughtersBeforeHadronization\":[";
  for (std::size_t i = 0; i < configured.daughters.size(); ++i) {
    if (i) out << ',';
    out << configured.daughters[i];
  }
  out << "],\"daughterVertices\":[";
  bool firstVertex = true;
  for (int daughter : p.daughterList()) {
    const Particle& child = event[daughter];
    if (!firstVertex) out << ',';
    firstVertex = false;
    out << "[" << child.xProd() << "," << child.yProd() << "," << child.zProd() << "," << child.tProd() << "]";
  }
  out << "]}";
}

static int configuredChannel(const std::vector<int>& daughters,
                             const std::vector<Channel>& channels) {
  for (std::size_t i = 0; i < channels.size(); ++i) {
    std::vector<int> left = daughters, right = channels[i].daughters;
    std::sort(left.begin(), left.end());
    std::sort(right.begin(), right.end());
    if (left == right) return static_cast<int>(i);
  }
  if (daughters.size() == 2) {
    for (std::size_t i = 0; i < channels.size(); ++i)
      if (channels[i].daughters == std::vector<int>{5, -5} &&
          !(std::abs(daughters[0]) == 22 && std::abs(daughters[1]) == 22)) return static_cast<int>(i);
  }
  return -1;
}

int main(int argc, char** argv) {
  try {
    if (hasArg(argc, argv, "--probe-pdg")) {
      Pythia probe;
      const int pdg = std::stoi(value(argc, argv, "--probe-pdg"));
      return probe.particleData.isParticle(pdg) ? 0 : 1;
    }
    const std::string lhe = value(argc, argv, "--lhe");
    const std::string output = value(argc, argv, "--out");
    const int events = std::stoi(value(argc, argv, "--events"));
    const int seed = std::stoi(value(argc, argv, "--seed"));
    const double mass = std::stod(value(argc, argv, "--mass"));
    const double ctau = std::stod(value(argc, argv, "--ctau"));
    const int productionEvents = std::stoi(value(argc, argv, "--production-events"));
    const std::string adapter = hasArg(argc, argv, "--cmnd") ? value(argc, argv, "--cmnd") : "";
    const bool isResonance = std::stoi(value(argc, argv, "--is-resonance")) != 0;
    const std::vector<Channel> channels = parseChannels(value(argc, argv, "--channels"));
    if (events <= 0 || productionEvents <= 0 || mass <= 0.0 || ctau <= 0.0)
      throw std::runtime_error("invalid numeric input");

    Pythia pythia;
    pythia.readString("Beams:frameType = 4");
    pythia.readString("Beams:LHEF = " + lhe);
    pythia.readString("SLHA:readFrom = 0");
    pythia.readString("LesHouches:setLifetime = 2");
    pythia.readString("Random:setSeed = on");
    pythia.readString("Random:seed = " + std::to_string(seed));
    pythia.readString("Next:numberShowEvent = 0");
    pythia.readString("Next:numberShowInfo = 0");
    pythia.readString("Next:numberShowProcess = 0");
    const double physicalWidth = 1.973269804e-13 / ctau;
    // Pythia's resonance-width table drops widths below its numerical floor;
    // tau0 remains the authoritative lifetime, while this tiny floor keeps the
    // A/B resonance path open for the requested one-event engineering test.
    const double width = isResonance ? std::max(physicalWidth, 1e-9) : physicalWidth;
    pythia.readString("9000006:all = h2 h2 1 0 0 " + std::to_string(mass) + " " + std::to_string(width) + " 0 0 " + std::to_string(ctau));
    pythia.readString("9000006:isResonance = " + std::string(isResonance ? "true" : "false"));
    pythia.readString("9000006:mayDecay = true");
    pythia.readString("9000006:tau0 = " + std::to_string(ctau));
    pythia.readString("ParticleDecays:limitTau0 = off");
    for (const Channel& channel : channels) {
      std::ostringstream setting;
      setting << "9000006:addChannel = 1 " << std::setprecision(17) << channel.br
              << ' ' << (isResonance ? 101 : 0);
      for (int daughter : channel.daughters) setting << ' ' << daughter;
      pythia.readString(setting.str());
    }
    if (!adapter.empty() && !pythia.readFile(adapter)) throw std::runtime_error("adapter .cmnd read failed");
    if (!pythia.init()) throw std::runtime_error("Pythia init failed");
    // LHE SLHA metadata may carry Pack A's historical width/lifetime. Pack AA's
    // declared lifetime is authoritative and must be applied after init.
    ParticleDataEntryPtr h2Data = pythia.particleData.particleDataEntryPtr(9000006);
    h2Data->clearChannels();
    for (const Channel& channel : channels) {
      h2Data->addChannel(1, channel.br, isResonance ? 101 : 0,
                         channel.daughters.size() > 0 ? channel.daughters[0] : 0,
                         channel.daughters.size() > 1 ? channel.daughters[1] : 0,
                         channel.daughters.size() > 2 ? channel.daughters[2] : 0,
                         channel.daughters.size() > 3 ? channel.daughters[3] : 0);
    }
    h2Data->rescaleBR();
    h2Data->setMayDecay(true);
    h2Data->setTau0(ctau);
    h2Data->setMWidth(width);
    h2Data->setTauCalc(!isResonance);
    pythia.particleData.resInit(9000006);
    // Resonance-width initialisation may derive tau0 from the numerical width
    // floor; restore the externally configured lifetime after that bookkeeping.
    h2Data->setTau0(ctau);

    std::ofstream out(output);
    if (!out) throw std::runtime_error("cannot open output " + output);
    out << std::setprecision(17);
    int processed = 0;
    int failed = 0;
    while (processed < events) {
      if (!pythia.next()) {
        ++failed;
        break;
      }
      ++processed;
      const int productionEventId = (processed - 1) % productionEvents + 1;
      const int replicaId = (processed - 1) / productionEvents;
      std::vector<int> h2Indices;
      for (int i = 0; i < pythia.event.size(); ++i)
        if (pythia.event[i].id() == 9000006) h2Indices.push_back(i);
      std::vector<std::pair<int, int>> physicalH2;
      for (int index : h2Indices) {
        std::vector<int> daughters;
        for (int daughter : pythia.event[index].daughterList()) daughters.push_back(pythia.event[daughter].id());
        const int channel = configuredChannel(daughters, channels);
        if (channel >= 0) physicalH2.push_back({index, channel});
      }
      out << "{\"schema\":\"pack_aa.truth.v1\",\"event\":" << processed
          << ",\"production_event_id\":" << productionEventId
          << ",\"replica_id\":" << replicaId
          << ",\"pythia_seed\":" << seed
          << ",\"pythia_rng_draw_index\":" << processed
          << ",\"weight\":" << pythia.info.weight()
          << ",\"sigmaGen_pb\":" << (pythia.info.sigmaGen() * 1e9)
          << ",\"h2BeforeCount\":" << physicalH2.size() << ",\"h2AllCount\":" << h2Indices.size()
          << ",\"h2AfterCount\":" << physicalH2.size()
          << ",\"h2All\":[";
      for (std::size_t h = 0; h < h2Indices.size(); ++h) {
        const Particle& history = pythia.event[h2Indices[h]];
        if (h) out << ',';
        out << "{\"index\":" << history.index() << ",\"status\":" << history.status()
            << ",\"tau\":" << history.tau() << ",\"hasVertex\":" << (history.hasVertex() ? "true" : "false")
            << ",\"xProd\":" << history.xProd() << ",\"daughters\":[";
        std::vector<int> historyDaughters;
        for (int daughter : history.daughterList()) historyDaughters.push_back(pythia.event[daughter].id());
        for (std::size_t j = 0; j < historyDaughters.size(); ++j) { if (j) out << ','; out << historyDaughters[j]; }
        out << "]}";
      }
      out << "],\"h2\":[";
      for (std::size_t h = 0; h < physicalH2.size(); ++h) {
        const Particle& parent = pythia.event[physicalH2[h].first];
        std::vector<int> daughters;
        for (int daughter : parent.daughterList()) daughters.push_back(pythia.event[daughter].id());
        writeH2(out, pythia.event, parent, daughters, channels[physicalH2[h].second], h == 0);
      }
      out << "]}\n";
    }
    out.close();
    std::ofstream meta(output + ".driver.json");
    meta << "{\n"
         << "  \"n_events_in\": " << events << ",\n"
         << "  \"n_events_out\": " << processed << ",\n"
         << "  \"n_events_failed_decay\": " << failed << ",\n"
         << "  \"n_events_filtered\": 0,\n"
         << "  \"filter_reasons\": [],\n"
         << "  \"seed\": " << seed << ",\n"
         << "  \"ctau_mm\": " << ctau << ",\n"
         << "  \"isResonance\": " << (isResonance ? "true" : "false") << "\n"
         << "}\n";
    return processed == events && failed == 0 ? 0 : 3;
  } catch (const std::exception& error) {
    std::cerr << "pack_aa_driver: " << error.what() << '\n';
    return 3;
  }
}
